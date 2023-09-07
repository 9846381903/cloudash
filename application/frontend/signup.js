function submitForm(event) {
    event.preventDefault();

    var username = document.getElementById('username').value;
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirm-password').value;

    if (password !== confirmPassword) {
        alert('Password and confirm password do not match!');
        return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://<public-ip-address>/v1/register', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        var response = JSON.parse(xhr.responseText);
        if (xhr.readyState == 4 && (xhr.status === 200 || xhr.status === 409)) {
            if ('error' in response) {
                alert('Signup failed! ' + response.error);
            } else {
                setTimeout(function() {
                    var otp = prompt('OTP sent to email for verification. Please enter the OTP');
                    verifyOtp(email, otp);
                }, 500);
            }
        } else {
            alert('Signup failed! Please try again');
        }
    };
    xhr.onerror = function() {
        alert('Request failed');
    };
    xhr.send(JSON.stringify({username: username, email: email, password: password, confirm_password: confirmPassword}));
}

document.getElementById('signup-form').removeEventListener('submit', submitForm);
document.getElementById('signup-form').addEventListener('submit', submitForm);

function verifyOtp(email, otp) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://<public-ip-address>/v1/verify-otp', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        var response = JSON.parse(xhr.responseText);
        if (xhr.readyState == 4 && xhr.status === 200) {
            if ('message' in response) {
                alert('Account created successful!');
                document.getElementById('signup-form').reset();
            } else {
                alert('Incorrect OTP. Please try again.');
            }
        } else {
            alert('OTP verification failed. Please try again.');
        }
    };
    xhr.onerror = function() {
        alert('Request failed');
    };
    xhr.send(JSON.stringify({email: email, otp: otp}));
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}
