// LingFlow自定义JavaScript

// 复制代码按钮
document.addEventListener('DOMContentLoaded', function() {
    // 为所有代码块添加复制按钮
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(function(codeBlock) {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.textContent = '复制';
        button.style.position = 'absolute';
        button.style.top = '0.5rem';
        button.style.right = '0.5rem';
        button.style.padding = '0.25rem 0.5rem';
        button.style.fontSize = '0.75rem';
        button.style.cursor = 'pointer';

        const pre = codeBlock.parentElement;
        pre.style.position = 'relative';
        pre.appendChild(button);

        button.addEventListener('click', function() {
            navigator.clipboard.writeText(codeBlock.textContent).then(function() {
                button.textContent = '已复制!';
                setTimeout(function() {
                    button.textContent = '复制';
                }, 2000);
            });
        });
    });

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // 外部链接打开新标签
    document.querySelectorAll('a.external').forEach(function(link) {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
});

// API搜索功能
function searchAPI() {
    const searchInput = document.getElementById('api-search');
    const searchText = searchInput.value.toLowerCase();

    document.querySelectorAll('.api-item').forEach(function(item) {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchText)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// 返回顶部按钮
window.addEventListener('scroll', function() {
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        if (window.pageYOffset > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    }
});
