export function applyEmbedMode() {
    const urlParams = new URLSearchParams(window.location.search);
    const embedValue = urlParams.get('embed');
    const isEmbed = embedValue === 'true' || embedValue === '1';

    document.body.classList.toggle('embed-mode', isEmbed);
    return isEmbed;
}
