let currentData = null;

async function fetchData() {
  try {
    const response = await fetch('api/getInfo');
    const data = await response.json();
    updateUI(data);
  } catch (error) {
    console.error('Ошибка получения данных:', error);
  }
}

setInterval(fetchData, 5000);

fetchData();

function updateUI(data) {
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
    
  const closeBtn = modal.querySelector('.close');
  closeBtn.onclick = function() {
    modal.style.display = 'none';
  };
  
  window.onclick = function(event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  };
  
  
  data.users.forEach(user => {
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
            try {
              const qrImage = modal.querySelector('#qrImage');
              
              qrImage.src = 'static/img/loading.gif';
              modal.style.display = 'block';
              
              const qrSrc = await loadQrCode(user);
              qrImage.src = qrSrc.qrcode;
              
            } catch (error) {
              console.error('Ошибка:', error);
              qrImage.src = 'static/img/error-qr.png';
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
          buttonDownload.className = 'btnDownload'

          buttonDownload.addEventListener('click', () => {
            downloadUserData(user);
          });
  
          const buttonDelete = document.createElement('button');
          const buttonDeleteA = document.createElement('a');
          const buttonDeleteImg = document.createElement('img');
          buttonDeleteImg.src = 'static/img/delete.png';
          buttonDeleteImg.alt = 'Delete';
          clientButtons.appendChild(buttonDelete);
          buttonDelete.appendChild(buttonDeleteA);
          buttonDeleteA.appendChild(buttonDeleteImg);
          buttonDelete.className = 'btnDelete'

          buttonDelete.addEventListener('click', () => {
            if (confirm(`Вы уверены, что хотите удалить пользователя ${user.name}?`)) {
              deleteUser(user.name);
            }})
  });
}

async function loadQrCode(user) {
  try {    
    const response = await fetch(`api/users/${user.name}/qrcode`);
    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }
    
    const dataQr = await response.json();

    return dataQr
    
  } catch (error) {
    console.error('Ошибка загрузки QR-кода:', error);
    return '../img/qr-kod-zaglushka.png';
  }
}

function downloadUserData(user) {
  const userData = JSON.stringify(user, null, 2);
  
  const blob = new Blob([userData], { type: 'application/json' });
  
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement('a');
  a.href = url;
  a.download = `conf_${user.name.replace(/ /g, '_')}.json`;
  
  // Добавляем ссылку в DOM и эмулируем клик
  document.body.appendChild(a);
  a.click();
  
  // Удаляем ссылку и освобождаем память
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
}

async function deleteUser(username) {
  try {

    const response = await fetch(`/api/users/${username}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username: username})
    });
    console.log(`Пользователь ${username} удален`);
    fetchData()
    
    
  } catch (error) {
    console.error('Ошибка при удалении пользователя:', error);
    alert('Не удалось удалить пользователя');
  }
}


// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  fetchData();
  setupModalHandlers();
});

// Настройка обработчиков модального окна
function setupModalHandlers() {
  const modal = document.getElementById('newUserModal');
  const btnNew = document.querySelector('.btnNew');
  const closeBtn = modal.querySelector('.close');
  
  btnNew.addEventListener('click', () => {
    modal.style.display = 'block';
  });
  
  closeBtn.addEventListener('click', () => {
    modal.style.display = 'none';
  });
  
  window.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
  
  document.getElementById('newUserForm').addEventListener('submit', (e) => {
    e.preventDefault();
    addNewUser();
  });
}

// Модифицированная функция addNewUser
async function addNewUser() {
  const nameInput = document.getElementById('userName');

    try {
    // 1. Отправляем данные на сервер
    const response = await fetch('/api/users', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username: nameInput.value.trim()})
    });

    if (!response.ok) throw new Error('Ошибка сервера');

    fetchData()
    
    // 4. Закрываем модалку
    document.getElementById('newUserModal').style.display = 'none';
    nameInput.value = '';
  
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Не удалось добавить пользователя');
  }
}
