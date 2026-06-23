const songCard = document.querySelector(".song-card")
const addCircle = document.querySelector(".add-circle")
const playlistModal = document.getElementById("playlistModal")
const closeTargets = document.querySelectorAll('[data-close-modal]')

const openModal = () =>{
    playlistModal.hidden = false
    playlistModal.setAttribute('aria-hidden', 'false')
}

const closeModal = () =>{
    playlistModal.hidden = true
    playlistModal.setAttribute('aria-hidden', 'true')
}

songCard.addEventListener('click', openModal)
    songCard.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openModal();
        }
    });
addCircle.addEventListener('click', (event) => {
    event.stopPropagation();
    openModal();
});

closeTargets.forEach((target) => target.addEventListener('click', closeModal));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !playlistModal.hidden) {
            closeModal();
        }
    });
