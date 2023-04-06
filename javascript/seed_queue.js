function getSeed() {
    var infoDivContent = document.querySelector("#html_info_txt2img").textContent;
    var seedRegex = /Seed:\s+(\d+)/;
    var seedMatch = infoDivContent.match(seedRegex);
    if (seedMatch) {
        var seed = seedMatch[1];
        var destSeedInput = Array.from(document.querySelectorAll('label span')).find(span => span.textContent === 'Seed(s) (Comma separated)').nextElementSibling;
        var seeds = destSeedInput.value.split(",").map(s => s.trim());
        if (seeds.includes(seed)) {
            alert("The seed already exists in the input.");
        } else {
            if (destSeedInput.value.trim() === "") {
                destSeedInput.value = seed;
            } else {
                destSeedInput.value += ", " + seed;
            }
        }
    } else {
        alert("No seed found in the output viewer.");
    }
}

function getPromptText() {
    var promptTextArea = document.querySelector('label textarea.autocomplete');
    return promptTextArea.value;
}
