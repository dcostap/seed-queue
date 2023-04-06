// Get the seed value
function getSeed() {
    const seed = Math.floor(Math.random() * (2 ** 32 - 1));
    const prompt = getPromptText();

    // Get the seed_prompt_table element and its current value
    const seedPromptTable = document.querySelector("table[data-testid='table']");
    const seedPromptTableValue = JSON.parse(seedPromptTable.getAttribute("value"));

    // Add the new seed and prompt pair to the table value
    seedPromptTableValue.push([seed.toString(), prompt, "<button class='delete-button'>Delete</button>"]);

    // Update the seed_prompt_table component's value
    seedPromptTable.setAttribute("value", JSON.stringify(seedPromptTableValue));

    // Register the delete button event listeners
    registerDeleteButtonListeners();
}

// Get the prompt text
function getPromptText() {
    const promptElement = document.querySelector('label span:is(.sr-only.hide) + textarea');
    return promptElement.value;
}

// Register delete button event listeners
function registerDeleteButtonListeners() {
    const deleteButtons = document.querySelectorAll(".delete-button");
    deleteButtons.forEach((button, index) => {
        button.removeEventListener("click", handleDeleteButtonClick);
        button.addEventListener("click", handleDeleteButtonClick);
    });
}

// Handle delete button click event
function handleDeleteButtonClick(event) {
    const seedPromptTable = document.querySelector("table[data-testid='table']");
    const seedPromptTableValue = JSON.parse(seedPromptTable.getAttribute("value"));
    const rowToDelete = event.target.closest("tr");

    // Find the index of the row to delete
    const rowIndexToDelete = Array.from(rowToDelete.parentElement.children).indexOf(rowToDelete);

    // Remove the row from the table value
    seedPromptTableValue.splice(rowIndexToDelete, 1);

    // Update the seed_prompt_table component's value
    seedPromptTable.setAttribute("value", JSON.stringify(seedPromptTableValue));
}

// Call registerDeleteButtonListeners after the page loads
window.addEventListener("DOMContentLoaded", () => {
    registerDeleteButtonListeners();
});