async function installOrsay(tvIP) {
    try {
        const response = await fetch(`http://${tvIP}:8080/install`, {
            method: 'POST',
            body: JSON.stringify({ image: 'orsay_firmware.img' }),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log('Install status:', data.status);
        alert('Прошивка Orsay установлена. TV перезагрузится.');
    } catch(e) {
        console.error(e);
        alert('Ошибка установки прошивки.');
    }
}
