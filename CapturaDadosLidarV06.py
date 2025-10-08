import os
import subprocess
import laspy
from ouster.sdk import sensor, core
from ouster.sdk.pcap import pcap, PcapPacketSource
from ouster.sdk.examples.pcap import pcap_to_csv
from datetime import datetime
from contextlib import closing
from more_itertools import time_limited
import pdal
import json

# -------- Configurações ----------
hostname = '169.254.11.136'
lidar_port = 7502
imu_port = 7503
n_seconds = 5  # tempo reduzido para teste
LASZIP_EXE = os.path.join(os.getcwd(), "laszip64")

# -------- Sensor config ----------
config = core.SensorConfig()
config.udp_profile_lidar = core.UDPProfileLidar.PROFILE_LIDAR_RNG19_RFL8_SIG16_NIR16
config.lidar_mode = core.LidarMode.MODE_2048x10
config.udp_port_lidar = lidar_port
config.udp_port_imu = imu_port
sensor.set_config(hostname, config, persist=True, udp_dest_auto=True)

# ----------------- Captura -----------------
with closing(sensor.SensorPacketSource(hostname, lidar_port=lidar_port, imu_port=imu_port,
                                       buffer_time_sec=1.0)) as source:

    meta = source.sensor_info[0]
    time_part = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname_base = f"{meta.prod_line}_{meta.sn}_{meta.config.lidar_mode}_{time_part}"
    folder_path = os.path.join("DadosLiDAR", fname_base)
    os.makedirs(folder_path, exist_ok=True)

    # salvar metadados
    json_path = os.path.join(folder_path, f"{fname_base}.json")
    with open(json_path, "w") as f:
        f.write(source.sensor_info[0].to_json_string())

    # capturar pcap
    pcap_path = os.path.join(folder_path, f"{fname_base}.pcap")
    source_it = time_limited(n_seconds, source)
    def to_packet():
        for idx, packet in source_it:
            yield packet
    n_packets = pcap.record(to_packet(), pcap_path)
    print(f'✔ Captured {n_packets} packets saved to "{pcap_path}"')

# ----------------- Gerar CSV do IMU usando pcap_to_csv -----------------
imu_csv_path = os.path.join(folder_path, f"{fname_base}_imu.csv")
print("▶ Gerando CSV do IMU com ouster-cli...")
try:
    subprocess.run([
        "ouster-cli", "source", pcap_path, "save", imu_csv_path
    ], check=True)
    print(f'✔ CSV do IMU gerado: {imu_csv_path}')
except subprocess.CalledProcessError as e:
    print(f'❌ Erro gerando CSV do IMU: {e}')
    imu_csv_path = None

# ----------------- Segunda leitura detalhada (opcional) -----------------
# Se você quiser processar pacotes frame a frame, pode manter:
source_detailed = PcapPacketSource(pcap_path)
metadata = source_detailed.sensor_info[0]
packet_format = core.PacketFormat(metadata)

# Exemplo de iteração frame a frame (Lidar + IMU)
for idx, packet in source_detailed:
    if isinstance(packet, core.LidarPacket):
        measurement_ids = packet_format.packet_header(core.ColHeader.MEASUREMENT_ID, packet.buf)
        timestamps = packet_format.packet_header(core.ColHeader.TIMESTAMP, packet.buf)
        ranges = packet_format.packet_field(core.ChanField.RANGE, packet.buf)
    elif isinstance(packet, core.ImuPacket):
        ax = packet_format.imu_la_x(packet.buf)
        ay = packet_format.imu_la_y(packet.buf)
        az = packet_format.imu_la_z(packet.buf)
        wx = packet_format.imu_av_x(packet.buf)
        wy = packet_format.imu_av_y(packet.buf)
        wz = packet_format.imu_av_z(packet.buf)

# ----------------- Conversão pcap → osf → las -----------------
osf_path = os.path.join(folder_path, f"{fname_base}.osf")
try:
    subprocess.run([
        "ouster-cli", "source", pcap_path, "slam",
        "--voxel-size", "0.0001",
        "save", osf_path
    ], check=True)
    print(f'✔ Converted "{pcap_path}" to "{osf_path}"')
except subprocess.CalledProcessError as e:
    print(f'❌ Error converting to .osf: {e}')
    exit(1)

las_path = os.path.join(folder_path, f"{fname_base}.las")
try:
    subprocess.run(["ouster-cli", "source", osf_path, "save", las_path], check=True)
    print(f'✔ Converted "{osf_path}" to "{las_path}"')
except subprocess.CalledProcessError as e:
    print(f'❌ Error converting to .las: {e}')
    exit(1)

# ----------------- Pipeline PDAL (antes do LAZ) -----------------
las_corrected = os.path.join(folder_path, f"{fname_base}_corrected.las")
pipeline_json = {
    "pipeline": [
        str(las_path),
        {
            "type": "filters.outlier",
            "method": "statistical",
            "mean_k": 8,
            "multiplier": 2.5
        },
        str(las_corrected)
    ]
}

try:
    print("▶ Executando pipeline PDAL...")
    pipeline = pdal.Pipeline(json.dumps(pipeline_json))
    pipeline.validate()
    pipeline.execute()
    print(f'✔ PDAL processado e salvo em "{las_corrected}"')
    las_to_compress = las_corrected
except Exception as e:
    print(f'⚠ PDAL falhou, mantendo LAS original: {e}')
    las_to_compress = las_path

# ----------------- Compressão LAS → LAZ com laszip64 -----------------
if os.path.isfile(las_to_compress):
    las_input = las_to_compress
else:
    base, ext = os.path.splitext(las_to_compress)
    las_input_alt = f"{base}-000{ext}"
    if os.path.isfile(las_input_alt):
        las_input = las_input_alt
    else:
        print(f"❌ Arquivo LAS não encontrado nem com -000: {las_to_compress}")
        exit(1)

laz_path = os.path.join(folder_path, f"{fname_base}.laz")
if os.path.isfile(LASZIP_EXE) and os.access(LASZIP_EXE, os.X_OK):
    print(f"▶ Compactando {las_input} → {laz_path}")
    try:
        subprocess.run(
            f'"{LASZIP_EXE}" -i "{las_input}" -o "{laz_path}"',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f'✔ Conversão concluída: {laz_path}')
    except subprocess.CalledProcessError as e:
        print(f'❌ Erro na conversão LAZ:\n{e.stderr}')
        exit(1)
else:
    print(f'❌ O executável laszip64 não foi encontrado ou não tem permissão de execução: {LASZIP_EXE}')
    exit(1)

print("✔ Fluxo finalizado.")

