function getSeed() {
    var infoDivContent = document.querySelector("#html_info_txt2img").textContent;
    var seedRegex = /Seed:\s+(\d+)/;
    var seedMatch = infoDivContent.match(seedRegex);
    if (seedMatch) {
        var seed = seedMatch[1];
        var destSeedInput = document.querySelector('[label="Seed(s) (Comma separated)"] input');
        if (destSeedInput.value.trim() === "") {
            destSeedInput.value = seed;
        } else {
            destSeedInput.value += ", " + seed;
        }
    } else {
        alert("No seed found in the output viewer.");
    }
}