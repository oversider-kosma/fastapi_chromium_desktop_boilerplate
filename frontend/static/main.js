document.addEventListener('DOMContentLoaded', async () => {
    const versionElement = document.getElementById('app-version');

    try {
        const response = await fetch('/getVersion');
        if (!response.ok) throw new Error('Network response was not ok');

        const data = await response.json();

        if (data.status === 'ok') {
            versionElement.textContent = data.version;
        } else {
            versionElement.textContent = 'Status error';
        }
    } catch (error) {
        console.error('Fetch error:', error);
        versionElement.textContent = 'Failed to load';
    }
});
