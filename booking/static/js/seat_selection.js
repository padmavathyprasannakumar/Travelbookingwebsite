(function(){
    const seatButtons = document.querySelectorAll('.seat:not(.booked)');
    const selectedInput = document.querySelector('#id_selected_seats');
    const selectedList = document.querySelector('#selectedList');
    const totalFare = document.querySelector('#totalFare');
    const selected = new Set();

    function render(){
        const seats = Array.from(selected).sort();
        selectedInput.value = seats.join(',');
        selectedList.textContent = seats.length ? seats.join(', ') : 'None';
        totalFare.textContent = (seats.length * window.SEAT_PRICE).toFixed(2);
    }

    seatButtons.forEach(button => {
        button.addEventListener('click', () => {
            const seat = button.dataset.seat;
            if(selected.has(seat)){
                selected.delete(seat);
                button.classList.remove('selected');
            }else{
                selected.add(seat);
                button.classList.add('selected');
            }
            render();
        });
    });
})();
