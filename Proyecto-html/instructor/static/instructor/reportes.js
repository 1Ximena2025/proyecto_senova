// Datos de ejemplo para los gráficos
window.addEventListener('DOMContentLoaded', function() {
    // Evidencias por Día
    new Chart(document.getElementById('evidenciasPorDia'), {
        type: 'bar',
        data: {
            labels: [11,12,13,14,15,16,17,18,19,20,21,22,23,24,25],
            datasets: [
                {
                    label: 'Nuevas',
                    backgroundColor: '#ffe082',
                    data: [20, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95]
                },
                {
                    label: 'Aprobadas',
                    backgroundColor: '#3bb2f6',
                    data: [15, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // Categorías de Evidencia
    new Chart(document.getElementById('categoriasEvidencia'), {
        type: 'doughnut',
        data: {
            labels: ['DEPOS', 'Givit', 'IFPI', 'Tuga', 'LEM'],
            datasets: [{
                data: [28, 28, 27, 20, 20],
                backgroundColor: ['#3bb2f6', '#ffe082', '#27ae60', '#ff6384', '#7c5fff']
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });

    // Estado de Evidencia
    new Chart(document.getElementById('estadoEvidencia'), {
        type: 'doughnut',
        data: {
            labels: ['Aprobadas', 'Nuevas', 'Rechazadas'],
            datasets: [{
                data: [64, 35, 11],
                backgroundColor: ['#27ae60', '#ffe082', '#ff6384']
            }]
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });

    // Evidencias por Usuario
    new Chart(document.getElementById('evidenciasPorUsuario'), {
        type: 'bar',
        data: {
            labels: ['Ana Perez', 'Carlos Gomez', 'Laura Torres', 'Devid Ruiz', 'Javier Morales'],
            datasets: [{
                label: 'Evidencias',
                backgroundColor: ['#3bb2f6', '#ffe082', '#27ae60', '#ff6384', '#7c5fff'],
                data: [32, 30, 28, 25, 22]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
});
