$wgListenPort = 56130
$wgIP = "94.232.248.61"
$wgPORT = 51835

# Получаем IP-адрес
$ipAddress = [System.Net.Dns]::GetHostAddresses($wgIP)[0]
$EndPoints = New-Object System.Net.IPEndPoint($ipAddress, $wgPORT)

# Создаем сокет
$Socket = New-Object System.Net.Sockets.UdpClient($wgListenPort)

# Подготавливаем сообщение
$messageBytes = [Text.Encoding]::ASCII.GetBytes(":)")

# Отправляем сообщение 5 раз
for ($i = 0; $i -lt 5; $i++) {
    $Socket.Send($messageBytes, $messageBytes.Length, $EndPoints) | Out-Null
}

# Закрываем сокет
$Socket.Close()
