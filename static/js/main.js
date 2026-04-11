document.getElementById("uploadForm").addEventListener("submit", function () {
    
    const loader = document.getElementById("loader");
    const btn = document.getElementById("submitBtn");

    // Show loader
    loader.classList.remove("hidden");

    // Disable button to prevent multiple clicks
    btn.disabled = true;
    btn.innerText = "Processing...";
});