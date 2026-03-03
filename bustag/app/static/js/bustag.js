$(function () {
    $('.coverimg').on('click', function () {
        $('#imglarge').attr('src', $(this).attr('src'));
        $('#imagemodal').modal('show');
    });

    $('#pagenav').on('change', function () {
        window.location = $(this).val();
    });

    // 隐私模式功能
    var PRIVACY_KEY = 'bustag_privacy_mode';

    // 获取隐私模式状态，默认为开启（true）
    function isPrivacyMode() {
        var stored = localStorage.getItem(PRIVACY_KEY);
        // 如果未设置，默认为开启隐私模式
        if (stored === null) {
            return true;
        }
        return stored === 'true';
    }

    // 设置隐私模式状态
    function setPrivacyMode(enabled) {
        localStorage.setItem(PRIVACY_KEY, enabled.toString());
        applyPrivacyMode(enabled);
    }

    // 应用隐私模式样式
    function applyPrivacyMode(enabled) {
        if (enabled) {
            $('body').addClass('privacy-mode');
            $('#privacy-switch').prop('checked', true);
        } else {
            $('body').removeClass('privacy-mode');
            $('#privacy-switch').prop('checked', false);
        }
    }

    // 初始化隐私模式
    function initPrivacyMode() {
        var privacyEnabled = isPrivacyMode();
        applyPrivacyMode(privacyEnabled);

        // 绑定切换事件
        $('#privacy-switch').on('change', function () {
            var enabled = $(this).prop('checked');
            setPrivacyMode(enabled);
        });
    }

    // 页面加载时初始化
    initPrivacyMode();
});
