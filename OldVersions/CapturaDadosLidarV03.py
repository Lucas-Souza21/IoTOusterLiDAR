import os
import subprocess
import laspy
from ouster.sdk import sensor, core
from ouster.sdk.pcap import pcap
import numpy as np
from datetime import datetime
from contextlib import closing
from more_itertools import time_limited

# Configurações do sensor:
hostname = '169.254.11.136'  # Endereço ou nome do sensor
lidar_port = 7502
imu_port = 7503
n_seconds = 10  # Tempo de captura em segundos

config = core.SensorConfig()
config.udp_profile_lidar = core.UDPProfileLidar.PROFILE_LIDAR_RNG19_RFL8_SIG16_NIR16
config.lidar_mode = core.LidarMode.MODE_1024x20
config.udp_port_lidar = lidar_port
config.udp_port_imu = imu_port

sensor.set_config(hostname, config, persist=True, udp_dest_auto=True)

# Captura dos dados do sensor:
with closing(sensor.SensorPacketSource(hostname, lidar_port=lidar_port, imu_port=imu_port,
            buffer_time_sec=1.0)) as source:
    
    # Criar nome base e pasta
    meta = source.sensor_info[0]
    time_part = datetime.now().strftime('%Y%m%d_%H%M%S')
    fname_base = f"{meta.prod_line}_{meta.sn}_{meta.config.lidar_mode}_{time_part}"
    folder_path = os.path.join("DadosLiDAR", fname_base)
    os.makedirs(folder_path, exist_ok=True)

    # Salvar metadados
    json_path = os.path.join(folder_path, f"{fname_base}.json")
    with open(json_path, "w") as f:
        f.write(source.sensor_info[0].to_json_string())

    # Captura e salva o arquivo .pcap
    pcap_path = os.path.join(folder_path, f'{fname_base}.pcap')
    source_it = time_limited(n_seconds, source)

    def to_packet():
        for idx, packet in source_it:
            yield packet

    n_packets = pcap.record(to_packet(), pcap_path)
    print(f'✔ Captured {n_packets} packets saved to "{pcap_path}"')

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
        
    # Caminho do executável laszip64
    laszip_exe = os.path.join(os.getcwd(), "./laszip64")
    
    # Verificar se o laszip64 existe e é executável
    if not os.path.isfile(laszip_exe) or not os.access(laszip_exe, os.X_OK):
        print(f"❌ laszip64 não encontrado ou sem permissão: {laszip_exe}")
        exit(1)
        
    # Define caminhos .las (com prioridade para versão -000) e .laz
    las_path = os.path.join(
        folder_path,
        f'{fname_base}-000.las' if os.path.exists(os.path.join(folder_path, f'{fname_base}-000.las')) 
        else f'{fname_base}.las'
    )
    laz_path = os.path.join(folder_path, f'{fname_base}.laz')
    
    print(f"Convertendo: {las_path} → {laz_path}")

    try:
        subprocess.run(
            f'"{laszip_exe}" -i "{las_path}" -o "{laz_path}"',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f'✔ Conversão concluída: {laz_path}')
    except subprocess.CalledProcessError as e:
        print(f'❌ Erro na conversão:\n{e.stderr}')
        exit(1)
    
    # Remover arquivos intermediários .pcap e .osf
    try:
        os.remove(pcap_path)
        print(f'🗑 Arquivo .pcap removido: {pcap_path}')
        os.remove(osf_path)
        print(f'🗑 Arquivo .osf removido: {osf_path}')
        os.remove(las_path)
        print(f'🗑 Arquivo .las removido: {las_path}')
    except Exception as e:
        print(f'⚠ Erro ao tentar remover arquivos intermediários: {e}')

