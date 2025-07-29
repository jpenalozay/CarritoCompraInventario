# Script para configurar conexión SSH a la máquina virtual remota

# Variables
$remoteIp = "192.168.2.150"
$localIp = "192.168.2.210"
$remoteUser = "jlpy"  # Usuario de la VM
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"

# Función para verificar si OpenSSH está instalado
function Check-OpenSSH {
    if (!(Get-Command ssh -ErrorAction SilentlyContinue)) {
        Write-Host "OpenSSH no está instalado. Instalando..."
        Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
    }
}

# Generar clave SSH si no existe
if (!(Test-Path $sshKeyPath)) {
    Write-Host "Generando clave SSH..."
    ssh-keygen -t rsa -b 4096 -f $sshKeyPath -N ""
}

# Copiar clave pública a la VM (requiere contraseña inicial)
Write-Host "Copiando clave pública a la VM. Ingresa la contraseña de $remoteUser@$remoteIp cuando se solicite."
ssh-copy-id $remoteUser@$remoteIp

# Configurar conexión sin contraseña
Write-Host "Probando conexión SSH sin contraseña..."
ssh $remoteUser@$remoteIp "echo Conexión exitosa"

# Instrucciones adicionales
Write-Host "
Configuración completada. Ahora puedes acceder a la VM con: ssh $remoteUser@$remoteIp"
Write-Host "Para integrar con el proyecto, agrega comandos específicos en este script según sea necesario."