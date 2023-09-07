let apiInProgress = {};
let activeApiRequests = 0;
let launchApiInProgress = false;

function fetchAndDisplayInstanceList() {
  let instanceList = document.getElementById('instanceList');
  instanceList.innerHTML = ''; 

  let username = localStorage.getItem('username');
  let usernameSpan = document.getElementById('username');
  usernameSpan.textContent = username ? `${username}` : '';

  let headers = new Headers();
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'GET',
    headers: headers,
    redirect: 'follow'
  };

  fetch("http://<public-ip-address>/v1/listinstances", requestOptions)
    .then(response => response.json())
    .then(data => {
      if (Array.isArray(data) && data.length > 0) {
        let table = document.createElement('table');
        let tableHeader = document.createElement('tr');
        tableHeader.innerHTML = `
            <th>Instance ID</th>
            <th>Public IP</th>
            <th>Status</th>
            <th>SSH Command</th>
            <th>Operation</th>
        `;
        table.appendChild(tableHeader);

        data.forEach(instance => {
          let tableRow = document.createElement('tr');
          let status = instance.IP ? 'Running' : 'Stopped';

          let truncatedInstanceId = instance.UNIQUE_ID.slice(-17);

          let ipDisplay = instance.IP ? instance.IP : '';
          let sshCommand = instance.IP ? `ssh ubuntu@${instance.IP}` : '';

          tableRow.innerHTML = `
              <td>${truncatedInstanceId}</td>
              <td>${ipDisplay}</td>
              <td>${status}</td>
              <td>${sshCommand}</td>
              <td>
                  <div class="operation-buttons">
                      ${instance.IP ? `<a id="rebootButton-${instance.UNIQUE_ID}" class="operation-button reboot-button" href="#" onclick="rebootVM('${instance.UNIQUE_ID}')">Reboot</a>` : ''}
                      ${instance.IP ? `<a id="stopButton-${instance.UNIQUE_ID}" class="operation-button stop-button" href="#" onclick="stopVM('${instance.UNIQUE_ID}')">Stop</a>` : ''}
                      ${!instance.IP ? `<a id="startButton-${instance.UNIQUE_ID}" class="operation-button start-button" href="#" onclick="startVM('${instance.UNIQUE_ID}')">Start</a>` : ''}
                      <a id="terminateButton-${instance.UNIQUE_ID}" class="operation-button terminate-button" href="#" onclick="terminateVM('${instance.UNIQUE_ID}')">Terminate</a>
                  </div>
                  <div id="loading-${instance.UNIQUE_ID}" class="loading" style="display: none;">
                      <img src="loading.gif" alt="Loading...">
                  </div>
              </td>
          `;
          table.appendChild(tableRow);
        });

        instanceList.appendChild(table);
      } else {
        let emptyListMessage = document.createElement('p');
        emptyListMessage.innerText = 'No virtual machines are launched.';
        emptyListMessage.className = 'empty-list-message';
        instanceList.appendChild(emptyListMessage);
      }
    })
    .catch(error => {
      console.log('error', error);
      window.location.href = "../login/"; 
    });
}

function rebootVM(uniqueId) {
  if (apiInProgress[uniqueId]) return;

  apiInProgress[uniqueId] = true;
  activeApiRequests++;

  let loading = document.getElementById(`loading-${uniqueId}`);
  let rebootButton = document.getElementById(`rebootButton-${uniqueId}`);
  let stopButton = document.getElementById(`stopButton-${uniqueId}`);
  let startButton = document.getElementById(`startButton-${uniqueId}`);
  let terminateButton = document.getElementById(`terminateButton-${uniqueId}`);

  loading.style.display = "block";
  loading.innerHTML = `<img src="operation.gif" alt="Operation in progress...">`;
  disableButtons(rebootButton, stopButton, startButton, terminateButton);

  let headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ unique_id: uniqueId }),
    redirect: 'follow'
  };

  fetch("http://<public-ip-address>/v1/rebootvm", requestOptions)
    .then(response => {
      if (response.ok) {
        console.log("Reboot VM API invoked successfully.");
        completeRequest(uniqueId);
      } else {
        console.log("Failed to invoke Reboot VM API.");
      }
    })
    .catch(error => {
      console.log('error', error);
      completeRequest(uniqueId);
    });
}

function stopVM(uniqueId) {
  if (apiInProgress[uniqueId]) return;

  apiInProgress[uniqueId] = true;
  activeApiRequests++;

  let loading = document.getElementById(`loading-${uniqueId}`);
  let rebootButton = document.getElementById(`rebootButton-${uniqueId}`);
  let stopButton = document.getElementById(`stopButton-${uniqueId}`);
  let startButton = document.getElementById(`startButton-${uniqueId}`);
  let terminateButton = document.getElementById(`terminateButton-${uniqueId}`);

  loading.style.display = "block";
  loading.innerHTML = `<img src="operation.gif" alt="Operation in progress...">`;
  disableButtons(rebootButton, stopButton, startButton, terminateButton);

  let headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ unique_id: uniqueId }),
    redirect: 'follow'
  };

  fetch("http://<public-ip-address>/v1/stopvm", requestOptions)
    .then(response => {
      if (response.ok) {
        console.log("Stop VM API invoked successfully.");
        completeRequest(uniqueId);
      } else {
        console.log("Failed to invoke Stop VM API.");
      }
    })
    .catch(error => {
      console.log('error', error);
      completeRequest(uniqueId);
    });
}

function startVM(uniqueId) {
  if (apiInProgress[uniqueId]) return;

  apiInProgress[uniqueId] = true;
  activeApiRequests++;

  let loading = document.getElementById(`loading-${uniqueId}`);
  let rebootButton = document.getElementById(`rebootButton-${uniqueId}`);
  let stopButton = document.getElementById(`stopButton-${uniqueId}`);
  let startButton = document.getElementById(`startButton-${uniqueId}`);
  let terminateButton = document.getElementById(`terminateButton-${uniqueId}`);

  loading.style.display = "block";
  loading.innerHTML = `<img src="operation.gif" alt="Operation in progress...">`;
  disableButtons(rebootButton, stopButton, startButton, terminateButton);

  let headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ unique_id: uniqueId }),
    redirect: 'follow'
  };

  fetch("http://<public-ip-address>/v1/startvm", requestOptions)
    .then(response => {
      if (response.ok) {
        console.log("Start VM API invoked successfully.");
        completeRequest(uniqueId);
      } else {
        console.log("Failed to invoke Start VM API.");
      }
    })
    .catch(error => {
      console.log('error', error);
      completeRequest(uniqueId);
    });
}

function terminateVM(uniqueId) {
  if (apiInProgress[uniqueId]) return;

  apiInProgress[uniqueId] = true;
  activeApiRequests++;

  let loading = document.getElementById(`loading-${uniqueId}`);
  let rebootButton = document.getElementById(`rebootButton-${uniqueId}`);
  let stopButton = document.getElementById(`stopButton-${uniqueId}`);
  let startButton = document.getElementById(`startButton-${uniqueId}`);
  let terminateButton = document.getElementById(`terminateButton-${uniqueId}`);

  loading.style.display = "block";
  loading.innerHTML = `<img src="operation.gif" alt="Operation in progress...">`;
  disableButtons(rebootButton, stopButton, startButton, terminateButton);

  let headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ unique_id: uniqueId }),
    redirect: 'follow'
  };

  fetch("http://<public-ip-address>/v1/terminatevm", requestOptions)
    .then(response => {
      if (response.ok) {
        console.log("Terminate VM API invoked successfully.");
        completeRequest(uniqueId);
      } else {
        console.log("Failed to invoke Terminate VM API.");
      }
    })
    .catch(error => {
      console.log('error', error);
      completeRequest(uniqueId);
    });
}

function disableButtons(rebootButton, stopButton, startButton, terminateButton) {
  if (rebootButton) {
    rebootButton.classList.add('disabled');
    rebootButton.disabled = true;
  }
  if (stopButton) {
    stopButton.classList.add('disabled');
    stopButton.disabled = true;
  }
  if (startButton) {
    startButton.classList.add('disabled');
    startButton.disabled = true;
  }
  if (terminateButton) {
    terminateButton.classList.add('disabled');
    terminateButton.disabled = true;
  }
}

function enableButtons(rebootButton, stopButton, startButton, terminateButton) {
  if (rebootButton) {
    rebootButton.classList.remove('disabled');
    rebootButton.disabled = false;
  }
  if (stopButton) {
    stopButton.classList.remove('disabled');
    stopButton.disabled = false;
  }
  if (startButton) {
    startButton.classList.remove('disabled');
    startButton.disabled = false;
  }
  if (terminateButton) {
    terminateButton.classList.remove('disabled');
    terminateButton.disabled = false;
  }
}

function completeRequest(uniqueId) {
  activeApiRequests--;
  if (activeApiRequests === 0 && !launchApiInProgress) {
    enableButtons(
      document.getElementById(`rebootButton-${uniqueId}`),
      document.getElementById(`stopButton-${uniqueId}`),
      document.getElementById(`startButton-${uniqueId}`),
      document.getElementById(`terminateButton-${uniqueId}`)
    );
    window.location.reload(); 
  }
}

function launchVM() {
  let launchButton = document.getElementById('launchButton');
  if (launchButton.disabled || launchApiInProgress) {
    return;
  }

  launchApiInProgress = true;

  let cpuBox = document.getElementById('cpuBox');
  let ramBox = document.getElementById('ramBox');
  let sshKeyBox = document.getElementById('sshKeyBox');
  let loading = document.getElementById('loading');

  let cpu = cpuBox.value;
  let ram = ramBox.value;
  let sshKey = sshKeyBox.value;

  let payload = {
    cpu: cpu,
    ram: ram,
    public_key: sshKey
  };

  let headers = new Headers();
  headers.append("Content-Type", "application/json");
  headers.append("Authorization", "Bearer " + localStorage.getItem('token'));

  let requestOptions = {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(payload),
    redirect: 'follow'
  };

  loading.style.display = "block";
  loading.innerHTML = `<img src="loading.gif" alt="Loading...">`;
  disableLaunchButton();

  fetch("http://<public-ip-address>/v1/launchvm", requestOptions)
    .then(response => response.text())
    .then(result => {
      console.log(result);
      loading.style.display = "none";
      cpuBox.value = "";
      ramBox.value = "";
      sshKeyBox.value = "";
      enableLaunchButton();
      launchApiInProgress = false;
      if (activeApiRequests === 0) {
        window.location.reload(); 
      }
    })
    .catch(error => {
      console.log('error', error);
      loading.style.display = "none";
      enableLaunchButton();
      launchApiInProgress = false;
    });
}

window.onload = function () {
  document.getElementById('logoutButton').addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = "../login/"; 
  });

  if (window.location.href.includes('/login/')) {
    window.location.reload();
  }

  document.getElementById('virtualMachinesButton').addEventListener('click', () => {
    let vmOptions = document.getElementById('vmOptions');
    vmOptions.style.display = vmOptions.style.display === "none" ? "block" : "none";
  });

  document.getElementById('launchButton').addEventListener('click', () => {
    launchVM();
  });

  document.getElementById('launchButton').addEventListener('dblclick', (event) => {
    event.preventDefault();
  });

  fetchAndDisplayInstanceList();
};

function disableLaunchButton() {
  let launchButton = document.getElementById('launchButton');
  launchButton.disabled = true;
}

function enableLaunchButton() {
  let launchButton = document.getElementById('launchButton');
  launchButton.disabled = false;
}

function checkApiInProgress() {
  for (let key in apiInProgress) {
    if (apiInProgress[key]) {
      return true;
    }
  }
  return false;
}
