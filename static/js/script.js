document.addEventListener('DOMContentLoaded', function () {
    // 모달 열기/닫기 관련 함수
    function openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
        }
    }

    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }

    // Upload 버튼 클릭 시 Upload 모달 열기
    const uploadButton = document.getElementById('openUploadModal');
    if (uploadButton) {
        uploadButton.addEventListener('click', function () {
            openModal('uploadModal');
        });
    }

    // Login 버튼 클릭 시 Login 모달 열기
    const loginButton = document.querySelector('.login-button');
    if (loginButton) {
        loginButton.addEventListener('click', function () {
            openModal('loginModal');
        });
    }

    // Signup 버튼 클릭 시 Signup 모달 열기
    const showSignupButton = document.getElementById('showSignupButton');
    if (showSignupButton) {
        showSignupButton.addEventListener('click', function () {
            closeModal('loginModal'); // Login 모달 닫기
            openModal('signupModal'); // Signup 모달 열기
        });
    }

    // 모든 close 버튼에 닫기 이벤트 추가
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const modal = button.closest('.modal, .chatmodal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });

    // 모달 외부 클릭 시 닫기
    window.addEventListener('click', function (event) {
        const modals = document.querySelectorAll('.modal, .chatmodal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });

    // 파일 업로드 처리
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            const formData = new FormData();
            formData.append('file', this.files[0]);

            // 업로드 진행 상태 표시
            const uploadMessage = document.getElementById('uploadMessage');
            if (uploadMessage) uploadMessage.textContent = '파일 업로드 중...';

            fetch('/upload/', {  // 서버의 업로드 URL로 변경 필요
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (uploadMessage) uploadMessage.textContent = data.message;
                })
                .catch(error => {
                    console.error('Error:', error);
                    if (uploadMessage) uploadMessage.textContent = '파일 업로드 중 오류가 발생했습니다.';
                });
        });
    }

    // 검색 폼 제출 이벤트 처리
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const searchQuery = this.querySelector('input[name="search_query"]').value;
            openChatModal(searchQuery);
        });
    }

    // Chat Modal 열기 함수
    function openChatModal(initialQuery = '') {
        openModal('chatModal');
        if (initialQuery) {
            const userInput = document.getElementById('user-input');
            if (userInput) {
                userInput.value = initialQuery;
                sendMessage();
            }
        }
    }

    // 메시지 전송 처리
    function sendMessage() {
        const userInput = document.getElementById('user-input');
        if (!userInput || !userInput.value.trim()) return;

        const modelSelect = document.getElementById('model-select');
        const model = modelSelect ? modelSelect.value : 'default';

        addMessage('user', userInput.value);

        fetch('/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ query: userInput.value, model: model })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage('system', data.error);
                } else {
                    addMessage('assistant', data.answer);
                    if (data.sources) addSources(data.sources);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage('system', '오류가 발생했습니다. 다시 시도해 주세요.');
            });

        userInput.value = '';
    }

    // 채팅 메시지 추가 함수
    function addMessage(role, content) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);

        // 스크롤을 최신 메시지로 이동
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 출처 추가 함수
    function addSources(sources) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        // 출처 컨테이너 생성
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';

        // 토글 버튼 생성
        const toggleButton = document.createElement('button');
        toggleButton.textContent = '참고한 페이지 보기';
        toggleButton.className = 'toggle-sources-btn';

        // 숨겨진 출처 내용 컨테이너 생성
        const sourcesContent = document.createElement('div');
        sourcesContent.className = 'sources-content';
        sourcesContent.style.display = 'none'; // 기본적으로 숨김

        // 출처 내용 추가
        sources.forEach((source, index) => {
            const sourceItem = document.createElement('p');
            sourceItem.innerHTML = `<strong>출처 ${index + 1}:</strong> ${source.source}<br>${source.text}...`;
            sourcesContent.appendChild(sourceItem);
        });

        // 토글 버튼 클릭 이벤트 추가
        toggleButton.addEventListener('click', function () {
            if (sourcesContent.style.display === 'none') {
                sourcesContent.style.display = 'block'; // 펼치기
                toggleButton.textContent = '참고한 페이지';
            } else {
                sourcesContent.style.display = 'none'; // 접기
                toggleButton.textContent = '참고한 페이지';
            }
        });

        // 출처 컨테이너에 버튼과 내용을 추가
        sourcesDiv.appendChild(toggleButton);
        sourcesDiv.appendChild(sourcesContent);

        // 채팅 메시지 영역에 출처 컨테이너 추가
        chatMessages.appendChild(sourcesDiv);

        // 스크롤을 최신 메시지로 이동
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // CSRF 토큰 가져오기 함수
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === `${name}=`) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const uploadName = document.querySelector('.upload-name'); // 파일 이름 표시 필드

    if (fileInput && uploadName) {
        fileInput.addEventListener('change', function () {
            const fileName = this.value.split("\\").pop(); // 파일 경로에서 파일명만 추출
            uploadName.value = fileName || "선택된 파일 없음"; // 선택된 파일 이름 표시
        });
    }
});
