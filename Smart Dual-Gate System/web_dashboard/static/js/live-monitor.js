(function () {
    const streamImage = document.getElementById("live-stream");

    if (!streamImage) return;

    streamImage.addEventListener("error", function () {
        streamImage.classList.add("stream-error");
        const offline = document.getElementById("stream-offline");
        if (offline) offline.classList.remove("d-none");
    });
})();
