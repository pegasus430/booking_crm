    function addevent(day,month,year){
        const newday =  String(day).padStart(2, '0');
        const newmonth = String(month).padStart(2, '0');
        var date = `${year}-${newmonth}-${newday}`
        document.getElementById("id_date").value=date;

        let modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('exampleModal'))
        modal.show();
    }
    
    function showEvents(day) {
        const eventsList = document.getElementById('events-list');
        const eventsContainer = document.getElementById('event-container-' + day);
        eventsList.innerHTML = ''; // Clear previous events
        if (eventsContainer) {
            // Get the content of the events container for the selected day
            const events = eventsContainer.innerHTML.trim();
            if (events) {
                // Update the events list widget with the events of the day
                eventsList.innerHTML = events;
            }
        }
    }

    // Add this event listener for the entire document to ensure all elements are loaded before attaching the click event
    document.addEventListener('DOMContentLoaded', function() {
        const dateElements = document.querySelectorAll('.date');
        dateElements.forEach(function(dateElement) {
            dateElement.addEventListener('click', function() {
                const day = parseInt(this.innerText); // Extract the day from the clicked element
                showEvents(day);
            });
        });
    });

    
