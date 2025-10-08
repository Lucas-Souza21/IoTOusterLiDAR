import os
import subprocess
import laspy
from ouster.sdk import sensor, core
from ouster.sdk.pcap import pcap
from datetime import datetime
from contextlib import closing
from more_itertools import time_limited
import pdal
import json

# -------- Configurações ----------
hostname = '169.254.11.136'
lidar_port = 7502
imu_port = 7503
n_seconds = 10  # tempo reduzido

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

    # converter pcap → osf
    osf_path = os.path.join(folder_path, f"{fname_base}.osf")
    try:
        subprocess.run([
            "ouster-cli", "source", pcap_path, "slam",
            "--voxel-size", "0.0001",  # voxel mínimo
            "save", osf_path
        ], check=True)
        print(f'✔ Converted "{pcap_path}" to "{osf_path}"')
    except subprocess.CalledProcessError as e:
        print(f'❌ Error converting to .osf: {e}')
        exit(1)

    # converter osf → las
    las_path = os.path.join(folder_path, f"{fname_base}.las")
    try:
        subprocess.run(["ouster-cli", "source", osf_path, "save", las_path], check=True)
        print(f'✔ Converted "{osf_path}" to "{las_path}"')
    except subprocess.CalledProcessError as e:
        print(f'❌ Error converting to .las: {e}')
        exit(1)

    # aplicar PDAL (apenas outlier filter para não depender de voxelgrid)
    las_filtered = os.path.join(folder_path, f"{fname_base}_filtered.las")
    pipeline_json = {
        "pipeline": [
            str(las_path),
            {
                "type": "filters.outlier",
                "method": "statistical",
                "mean_k": 8,
                "multiplier": 2.5
            },
            str(las_filtered)
        ]
    }

    try:
        print("▶ Executando pipeline PDAL...")
        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        pipeline.validate()
        pipeline.execute()
        print(f'✔ PDAL processado e salvo em "{las_filtered}"')
        las_to_compress = las_filtered
    except Exception as e:
        print(f'⚠ PDAL falhou, mantendo LAS original: {e}')
        las_to_compress = las_path

    # -------- Compressão LAS → LAZ com laszip64 --------
    # Ajuste para lidar com arquivo -000.las
    if os.path.isfile(las_to_compress):
        las_input = las_to_compress
    else:
        # tenta substituir .las por -000.las
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
