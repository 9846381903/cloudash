document.getElementById('login-form').addEventListener('submit', function(event) {
  event.preventDefault();
  var username_or_email = document.getElementById('username').value;
  var password = document.getElementById('password').value;
  var xhr = new XMLHttpRequest();
  xhr.open('POST', 'http://<public-ip-address>/v1/authenticate', true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  xhr.onload = function () {
    var response = JSON.parse(xhr.responseText);
    if (xhr.status === 200 && response.authenticated) {
      alert('Successfully logged in!');
      localStorage.setItem('token', response.token);
      localStorage.setItem('username', response.username);
      localStorage.setItem('email', response.email);
      window.location.href = "../console/";
    } else {
      if (xhr.status === 401) {
        alert('Incorrect password');
      } else if (xhr.status === 400 && response.error === 'User Not Found') {
        alert('User not found');
      } else {
        var errorMessage = response.error || 'Login failed';
        alert('Login failed! ' + errorMessage);
      }
    }
  };
  xhr.onerror = function() {
    alert('Request failed');
  };
  xhr.send(JSON.stringify({username_or_email: username_or_email, password: password}));
});
