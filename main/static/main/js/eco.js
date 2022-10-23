let intervalId;

document.querySelectorAll('.dropdown-toggle').forEach(e => {
    e.addEventListener('click', e => {
        const menu = e.currentTarget.dataset.path;
        // console.log(menu);
        document.querySelectorAll('.dropdown-menu').forEach(e => {
            if (!document.querySelector(`[data-target="${menu}"]`).classList.contains('open')) {
                document.querySelector(`[data-target="${menu}"]`).classList.add('menu-active');
                intervalId = setTimeout(() =>{
                    document.querySelector(`[data-target="${menu}"]`).classList.add('open');
                }, 0);
            }
            if (document.querySelector(`[data-target="${menu}"]`).classList.contains('open')){
                clearTimeout(intervalId);
                document.querySelector(`[data-target="${menu}"]`).classList.remove('menu-active');
                intervalId = setTimeout(() => {
                    document.querySelector(`[data-target="${menu}"]`).classList.remove('open');
                }, 0);
            }
        });
    });
});