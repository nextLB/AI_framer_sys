$(document).ready(function() {
    console.log('System initialized');
    
    $('.dropdown-toggle').dropdown();
    
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    setInterval(updateDeviceStatus, 30000);
});

function updateDeviceStatus() {
    $.get('/monitoring/devices/status/', function(data) {
        console.log('Device status updated');
    });
}

function showNotification(message, type = 'info') {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(alertHtml);
    setTimeout(() => $('.alert').alert('close'), 5000);
}

function sendControlCommand(deviceId, command) {
    $.post(`/control/${deviceId}/command/`, {
        command_type: command,
        csrfmiddlewaretoken: getCsrfToken()
    }, function(response) {
        showNotification('命令已发送', 'success');
    }).fail(function() {
        showNotification('命令发送失败', 'danger');
    });
}

function getCsrfToken() {
    return $('input[name="csrfmiddlewaretoken"]').val();
}