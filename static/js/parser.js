// ===== ОСТАЛЬНАЯ ЛОГИКА ПАРСЕРА =====
let currentJobId = null;
let statusCheckInterval = null;

// Быстрые примеры
document.querySelectorAll('.example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.getElementById('searchText').value = btn.dataset.value;
        const input = document.getElementById('searchText');
        input.style.transform = 'scale(1.02)';
        setTimeout(() => {
            input.style.transform = '';
        }, 200);
    });
});

// Дебаунс для загрузки городов
let cityTimeout;
const cityInput = document.getElementById('city');
if (cityInput) {
    cityInput.addEventListener('input', (e) => {
        clearTimeout(cityTimeout);
        cityTimeout = setTimeout(() => loadCities(e.target.value), 300);
    });
}

async function loadCities(query) {
    if (query.length < 2) return;
    try {
        const response = await fetch(`/api/regions?q=${encodeURIComponent(query)}`);
        const cities = await response.json();
        const datalist = document.getElementById('cities');
        datalist.innerHTML = '';
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city.name;
            datalist.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading cities:', error);
    }
}

const form = document.getElementById('parsingForm');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const startBtn = document.getElementById('startBtn');
        const originalText = startBtn.innerHTML;
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="loading-spinner"></span> Запуск...';

        const progressSection = document.getElementById('progressSection');
        const downloadSection = document.getElementById('downloadSection');
        progressSection.classList.add('active');
        downloadSection.classList.remove('active');

        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';

        const formData = {
            search_text: document.getElementById('searchText').value.trim(),
            city: document.getElementById('city').value.trim(),
            max_vacancies: parseInt(document.getElementById('maxVacancies').value) || 100,
            experience: document.getElementById('experience').value || null,
            salary: document.getElementById('salary').value ? parseInt(document.getElementById('salary').value) : null,
            format: document.getElementById('format').value
        };

        if (!formData.search_text) {
            showStatus('error', '❌ Пожалуйста, введите ключевое слово для поиска');
            startBtn.disabled = false;
            startBtn.innerHTML = originalText;
            return;
        }

        try {
            const response = await fetch('/api/start_parsing', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Unknown error');
            }

            currentJobId = data.job_id;
            startStatusCheck();

        } catch (error) {
            showStatus('error', '❌ Ошибка: ' + error.message);
            startBtn.disabled = false;
            startBtn.innerHTML = originalText;
        }
    });
}

function startStatusCheck() {
    if (statusCheckInterval) clearInterval(statusCheckInterval);
    statusCheckInterval = setInterval(checkStatus, 2000);
    checkStatus();
}

async function checkStatus() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/job_status/${currentJobId}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Status check failed');
        }

        const progressBar = document.getElementById('progressBar');
        const progress = data.progress || 0;
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${Math.round(progress)}%`;

        let statusText = '';
        switch (data.status) {
            case 'waiting':
                statusText = '⏳ Ожидание начала...';
                break;
            case 'running':
                statusText = '🔍 Парсинг выполняется... ' + (data.message || 'Это может занять несколько минут');
                break;
            case 'completed':
                statusText = `✅ Парсинг завершен! Найдено ${data.vacancies_count || 0} вакансий.`;
                const downloadSection = document.getElementById('downloadSection');
                downloadSection.classList.add('active');
                clearInterval(statusCheckInterval);
                const startBtn = document.getElementById('startBtn');
                startBtn.disabled = false;
                startBtn.innerHTML = '🚀 Новый поиск';
                break;
            case 'error':
                statusText = `❌ Ошибка: ${data.error_message || 'Неизвестная ошибка'}`;
                clearInterval(statusCheckInterval);
                const errorStartBtn = document.getElementById('startBtn');
                errorStartBtn.disabled = false;
                errorStartBtn.innerHTML = '🚀 Начать парсинг';
                break;
        }

        showStatus(data.status, statusText);

        if (data.status === 'completed' || data.status === 'error') {
            clearInterval(statusCheckInterval);
        }

    } catch (error) {
        console.error('Status check error:', error);
    }
}

function showStatus(status, message) {
    const statusDiv = document.getElementById('statusMessage');
    if (statusDiv) {
        statusDiv.className = `status ${status}`;
        statusDiv.textContent = message;
    }
}

const downloadBtn = document.getElementById('downloadBtn');
if (downloadBtn) {
    downloadBtn.addEventListener('click', async () => {
        if (!currentJobId) return;

        try {
            downloadBtn.innerHTML = '⏳ Загрузка...';
            downloadBtn.disabled = true;

            window.location.href = `/api/download/${currentJobId}`;

            setTimeout(() => {
                downloadBtn.innerHTML = '📥 Скачать файл';
                downloadBtn.disabled = false;
            }, 2000);
        } catch (error) {
            alert('Ошибка скачивания: ' + error.message);
            downloadBtn.innerHTML = '📥 Скачать файл';
            downloadBtn.disabled = false;
        }
    });
}

window.addEventListener('beforeunload', () => {
    if (currentJobId) {
        fetch('/api/cleanup', {method: 'POST'}).catch(console.error);
    }
});

document.querySelectorAll('input, select').forEach(el => {
    el.addEventListener('focus', () => {
        el.parentElement?.classList.add('focused');
    });
    el.addEventListener('blur', () => {
        el.parentElement?.classList.remove('focused');
    });
});

const searchTextInput = document.getElementById('searchText');
if (searchTextInput) {
    const lastSearch = localStorage.getItem('lastSearch');
    if (lastSearch) {
        searchTextInput.value = lastSearch;
    }
    searchTextInput.addEventListener('change', () => {
        localStorage.setItem('lastSearch', searchTextInput.value);
    });
}