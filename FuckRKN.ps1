$wgListenPort = 56130
$wgIP = "94.232.248.61"
$wgPORT = 51835

# �������� IP-�����
$ipAddress = [System.Net.Dns]::GetHostAddresses($wgIP)[0]
$EndPoints = New-Object System.Net.IPEndPoint($ipAddress, $wgPORT)

# ������� �����
$Socket = New-Object System.Net.Sockets.UdpClient($wgListenPort)

# �������������� ���������
$messageBytes = [Text.Encoding]::ASCII.GetBytes(":)")

# ���������� ��������� 5 ���
for ($i = 0; $i -lt 5; $i++) {
    $Socket.Send($messageBytes, $messageBytes.Length, $EndPoints) | Out-Null
}

# ��������� �����
$Socket.Close()
