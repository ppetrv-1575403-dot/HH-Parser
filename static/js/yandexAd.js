bannerAdId_top = ""
bannerAdId_native = ""
bannerAdId_bottom = ""

adTopContainerId = "yandexAdTop"
adNativeContainerId = "yandexAdNative"
adBottomContainerId = "yandexAdBottom"

adTopUiItemId = "yandex_rtb_R-A-XXXXXXXX-X"
adNativeUiItemId = "yandex_rtb_R-A-XXXXXXXX-X-native"
adBottomUiItemId = "yandex_rtb_R-A-XXXXXXXX-X-bottom"

function loadYandexAd(bannerAdId, // "R-A-XXXXXXXX-X" ★ ЗАМЕНИТЕ НА ВАШ ID ★
                      bannerType, // "floorAd"
                      uiControlId, // "yandex_rtb_R-A-XXXXXXXX-X-bottom",
                      containerId
) {
    if (!bannerAdId) {
        closeYandexAd(bannerAdId, false)
        hideAdContainer(containerId)
        return
    }
    window.yaContextCb.push(() => {
        Ya.Context.AdvManager.render({
            "blockId": bannerAdId,
            "renderTo": uiControlId,
            "type": bannerType
        })
    })
}

function hideAdContainer(cId) {
    const adElement = document.getElementById(cId);
    if (adElement) {
        adElement.remove()
    }
}

// ===== НАСТРОЙКИ ЯНДЕКС.РСЯ =====
// Закрытие рекламных блоков с сохранением состояния
function closeYandexAd(adId, fadeAnim) {
    const adElement = document.getElementById(adId);
    if (adElement) {
        if (!fadeAnim) {
            adElement.remove();
            // Сохраняем состояние закрытого блока
            rememberAdItemState(adId)
        } else {
            adElement.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                adElement.remove();
                // Сохраняем состояние закрытого блока
                rememberAdItemState(adId)
            }, 300);
        }
    }
}

// Сохраняем состояние закрытого блока
function rememberAdItemState(adId) {
     const closedAds = JSON.parse(localStorage.getItem('closedYandexAds') || '{}');
     closedAds[adId] = true;
     localStorage.setItem('closedYandexAds', JSON.stringify(closedAds));
}

// Загрузка состояния закрытых баннеров
(function loadYandexAdState() {
    const closedAds = JSON.parse(localStorage.getItem('closedYandexAds') || '{}');
    if (closedAds.yandexAdTop) document.getElementById('yandexAdTop')?.remove();
    if (closedAds.yandexAdNative) document.getElementById('yandexAdNative')?.remove();
    if (closedAds.yandexAdBottom) document.getElementById('yandexAdBottom')?.remove();
    if (closedAds.middleBanner) document.getElementById('middleBanner')?.remove();
})();

// Отложенная загрузка рекламы для улучшения производительности
// (реклама загружается асинхронно и не блокирует основной контент)
window.addEventListener('load', () => {
    // Яндекс.РСЯ сам загружает рекламу через window.yaContextCb
    console.log('Яндекс.РСЯ загружен');
});