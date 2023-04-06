var selectedSeed = null;

function storeCurrentPreviewInfo() {
    var infoDivContent = document.querySelector("#html_info_txt2img").textContent;
    var seedRegex = /Seed:\s+(\d+)/;
    var seedMatch = infoDivContent.match(seedRegex);
    if (seedMatch) {
        var seed = seedMatch[1];
        var promptText = getPromptText();
        if (promptText == null)
            return;

        // Add the seed and promptText to the hidden input as a JSON object
        var hiddenInput = document.querySelector("#hidden_prompt_seed_pairs_input textarea[data-testid='textbox']");
        var seedPromptPairs = JSON.parse(hiddenInput.value.replace(/<json>/g, ''));

        var existingPairIndex = seedPromptPairs.findIndex(pair => pair.seed === seed);
        if (existingPairIndex > -1) {
            seedPromptPairs[existingPairIndex].prompt = promptText;
        } else {
            seedPromptPairs.push({seed: seed, prompt: promptText});
        }

        hiddenInput.value = "<json>" + JSON.stringify(seedPromptPairs) + "<json>";

        // Add the seed to the visible list
        var seedList = document.getElementById("seed_list");
        var li = document.createElement("li");
        li.textContent = seed;
        li.onclick = function () {
            setSelectedSeed(seed);
        };

        if (existingPairIndex > -1) {
            seedList.replaceChild(li, seedList.children[existingPairIndex]);
        } else {
            seedList.appendChild(li);
        }

    } else {
        alert("No seed found in the output viewer.");
    }
}


function getPromptText() {
    var infoDivContent = document.querySelector("#html_info_txt2img").textContent;
    var negativePromptIndex = infoDivContent.indexOf("\nNegative prompt:");
    if (negativePromptIndex >= 0) {
        return infoDivContent.slice(0, negativePromptIndex);
    } else {
        alert("Error: Negative prompt not found in output viewer.");
        return null;
    }
}

function setSelectedSeed(seed) {
    selectedSeed = seed;
    updateSelectedSeedUI(seed);
}

function updateSelectedSeedUI(seed) {
    var seedList = document.getElementById("seed_list");
    var items = seedList.getElementsByTagName("li");
    for (var i = 0; i < items.length; i++) {
        if (items[i].textContent === seed) {
            items[i].style.backgroundColor = "lightblue";
        } else {
            items[i].style.backgroundColor = "";
        }
    }
}

function deleteSeed() {
    if (selectedSeed !== null) {
        // Remove the selected seed from the JSON object in the hidden Textbox
        var hiddenInput = document.querySelector("#hidden_prompt_seed_pairs_input textarea[data-testid='textbox']");
        var seedPromptPairs = JSON.parse(hiddenInput.value.replace(/<json>/g, ''));

        seedPromptPairs = seedPromptPairs.filter(pair => pair.seed !== selectedSeed);
        hiddenInput.value = "<json>" + JSON.stringify(seedPromptPairs) + "<json>";

        // Remove the selected seed from the list element
        var seedList = document.getElementById("seed_list");
        var items = seedList.getElementsByTagName("li");
        for (var i = 0; i < items.length; i++) {
            if (items[i].textContent === selectedSeed) {
                seedList.removeChild(items[i]);
                break;
            }
        }

        // Reset the selectedSeed variable
        selectedSeed = null;
    } else {
        alert("Please select a seed to delete.");
    }
}


function deleteAllSeeds() {
    // Clear the JSON object in the hidden Textbox
    var hiddenInput = document.querySelector("#hidden_prompt_seed_pairs_input textarea[data-testid='textbox']");
    hiddenInput.value = "";

    // Clear the list element
    var seedList = document.getElementById("seed_list");
    while (seedList.firstChild) {
        seedList.removeChild(seedList.firstChild);
    }

    // Reset the selectedSeed variable
    selectedSeed = null;
}

