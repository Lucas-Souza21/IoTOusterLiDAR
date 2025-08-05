import os
import subprocess
import laspy
from ouster.sdk import sensor, core, pcap
import numpy as np
from datetime import datetime
from contextlib import closing
from more_itertools import time_limited

# Configurações do sensor:
hostname = 'os-122308002238.local'
lidar_port = 7502
imu_port = 7503
n_seconds = 10# Tempo de captura em segundos

config = core.SensorConfig()
config.udp_profile_lidar = core.UDPProfileLidar.PROFILE_LIDAR_RNG19_RFL8_SIG16_NIR16  # ✅ Compatível com 1024x20
config.lidar_mode = core.LidarMode.MODE_1024x20  # ✅ Resolução maior
config.udp_port_lidar = lidar_port
config.udp_port_imu = imu_port

sensor.set_config(hostname, config, persist=True, udp_dest_auto=True)

# Captura dos dados do sensor:
with closing(sensor.SensorPacketSource(hostname, lidar_port=lidar_port, imu_port=imu_port,
                        buffer_time_sec=1.0)) as source:
    meta = source.sensor_info[0]
    time_part = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname_base = f'{meta.prod_line}_{meta.sn}{meta.config.lidar_mode}_{time_part}'
    folder_path = os.path.join("DadosLiDAR", fname_base)
    os.makedirs(folder_path, exist_ok=True)  # Criar diretório

    # Salvar metadados
    json_path = os.path.join(folder_path, f'{fname_base}.json')
    with open(json_path, 'w') as f:
        f.write(meta.to_json_string())

    # Captura e salva o arquivo .pcap
    pcap_path = os.path.join(folder_path, f'{fname_base}.pcap')
    source_it = time_limited(n_seconds, source)
    num_packets = pcap.record(
        source_it, pcap_path,
        src_ip='169.254.11.136', dst_ip='169.254.11.136',
        lidar_port=lidar_port, imu_port=imu_port)
    print(f'✔ Captured {num_packets} packets saved to "{pcap_path}"')

    # Converter .pcap para .osf
    osf_path = os.path.join(folder_path, f'{fname_base}.osf')
    try:
        subprocess.run(["ouster-cli", "source", pcap_path, "slam", "save", osf_path], check=True)
        print(f'✔ Converted "{pcap_path}" to "{osf_path}"')
    except subprocess.CalledProcessError as e:
        print(f'❌ Error converting to .osf: {e}')
        exit(1)

    # Converter .osf para .las
    las_path = os.path.join(folder_path, f'{fname_base}.las')
    try:
        subprocess.run(["ouster-cli", "source", osf_path, "save", las_path], check=True)
        print(f'✔ Converted "{osf_path}" to "{las_path}"')
    except subprocess.CalledProcessError as e:
        print(f'❌ Error converting to .las: {e}')
        exit(1)
