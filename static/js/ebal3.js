let currentData = null;

async function fetchData() {
  try {
    const response = await fetch('api/getInfo');
    const data = await response.json();
    await updateUI(data);
  } catch (error) {
    console.error('Ошибка получения данных:', error);
  }
}

setInterval(fetchData, 1000);

fetchData();

async function updateUI(data) {
  const container = document.getElementById('clients-list');
  
  if (JSON.stringify(data) === JSON.stringify(currentData)) return;

  currentData = data;

  container.innerHTML = '';

  let modal = document.getElementById('qrModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'qrModal';
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <span class="close">&times;</span>
        <img id="qrImage" src="" alt="QR Code">
      </div>
    `;
    document.body.appendChild(modal);
  }
    
  // Добавляем обработчики для закрытия модального окна
  const closeBtn = modal.querySelector('.close');
  closeBtn.onclick = function() {
    modal.style.display = 'none';
  };
  
  window.onclick = function(event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  };
  
  
  data.users.forEach(async user => {
    const clientDiv = document.createElement('div');
          container.appendChild(clientDiv);
          clientDiv.className = 'client-card';
  
          const clientContentDiv = document.createElement('div')
          clientDiv.appendChild(clientContentDiv)
          clientContentDiv.className = 'client-content'
  
          const clientInfo = document.createElement('div');
          clientContentDiv.appendChild(clientInfo);
          clientInfo.className = 'client-info';
          
          const clientImg = document.createElement('img');
          clientImg.src = 'static/img/user.png';
          clientImg.alt = 'User';
          clientInfo.appendChild(clientImg);
  
          const clientName = document.createElement('span');
          clientName.textContent = user.name;
          clientInfo.appendChild(clientName);
  
          const clientIP = document.createElement('span');
          clientIP.textContent = user.allowedIPs;
          clientInfo.appendChild(clientIP);
  
          if (user.isEnable == true) {
            const clientSpeedContainer = document.createElement('div');
            clientContentDiv.appendChild(clientSpeedContainer);
            clientSpeedContainer.className = 'client-speed'
  
            const clientRecieved = document.createElement('span');
            clientRecieved.textContent = user.received;
            const clientSend = document.createElement('span');
            clientSend.textContent = user.send;
            const clientHandshake = document.createElement('span');
            clientHandshake.textContent = user.latestHandshake;
  
            clientSpeedContainer.appendChild(clientRecieved);
            clientSpeedContainer.appendChild(clientSend);
            clientSpeedContainer.appendChild(clientHandshake);
          }
  
          const clientButtons = document.createElement('div');
          clientDiv.appendChild(clientButtons);
          clientButtons.className = 'client-buttons';
  
          const buttonOnOff = document.createElement('button');
          clientButtons.appendChild(buttonOnOff);
          buttonOnOff.className = 'button-on-off';
  
          const buttonOnOffCircle = document.createElement('div');
          buttonOnOff.appendChild(buttonOnOffCircle)
          buttonOnOffCircle.className = 'circle'
  
          if (user.isEnable == true) {
            buttonOnOff.classList.toggle('active');
          }
  
          buttonOnOff.addEventListener('click', function () {
            const isCurrentlyActive = this.classList.contains('active');
            const newStatus = !isCurrentlyActive;
          
            // Временно меняем визуально
            this.classList.toggle('active');
          
            fetch(`api/users/${encodeURIComponent(user.name)}/status`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ enable: newStatus })
            })
            .then(response => {
              if (!response.ok) {
                return response.text().then(text => {
                  throw new Error(`HTTP ${response.status}: ${text}`);
                });
              }
              return response.json();
            })
            .then(data => {
              console.log(`Ответ от сервера:`, data);
          
              // Применяем фактическое состояние, которое вернул сервер
              if (data.isEnable === true) {
                buttonOnOff.classList.add('active');
              } else {
                buttonOnOff.classList.remove('active');
              }
            })
            .catch(error => {
              console.error(`Ошибка при переключении пользователя ${user.name}:`, error);
              // Откатываем состояние
              if (newStatus) {
                this.classList.remove('active');
              } else {
                this.classList.add('active');
              }
            });
          });
  
          const buttonQR = document.createElement('button');
          const buttonQRA = document.createElement('a');
          const buttonQRImg = document.createElement('img');
          buttonQRImg.src = 'static/img/qr.png';
          buttonQRImg.alt = 'QR';
          clientButtons.appendChild(buttonQR);
          buttonQR.appendChild(buttonQRA);
          buttonQRA.appendChild(buttonQRImg);
          
          

          buttonQR.addEventListener('click', async function() {
            const response = await fetch(`/api/users/${user.name}/qrcode`);
            const dataQr = response.json();
            if (dataQr.status == 'success'){
              qrSrc = data.qrcode
              const qrImage = modal.querySelector('#qrImage');
              qrImage.src = qrSrc;
              modal.style.display = 'block';
            }
            
          });

          buttonQR.className = 'showQrBtn'
  
          const buttonDownload = document.createElement('button');
          const buttonDownloadA = document.createElement('a');
          const buttonDownloadImg = document.createElement('img');
          buttonDownloadImg.src = 'static/img/download.jpg';
          buttonDownloadImg.alt = 'Download';
          clientButtons.appendChild(buttonDownload);
          buttonDownload.appendChild(buttonDownloadA);
          buttonDownloadA.appendChild(buttonDownloadImg);
  
          const buttonDelete = document.createElement('button');
          const buttonDeleteA = document.createElement('a');
          const buttonDeleteImg = document.createElement('img');
          buttonDeleteImg.src = 'static/img/delete.png';
          buttonDeleteImg.alt = 'Delete';
          clientButtons.appendChild(buttonDelete);
          buttonDelete.appendChild(buttonDeleteA);
          buttonDeleteA.appendChild(buttonDeleteImg);
  });
}