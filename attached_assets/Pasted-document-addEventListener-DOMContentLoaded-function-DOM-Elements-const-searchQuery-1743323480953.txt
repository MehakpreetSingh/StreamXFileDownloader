document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const searchQueryInput = document.getElementById('searchQuery');
    const searchBtn = document.getElementById('searchBtn');
    const searchLoading = document.getElementById('searchLoading');
    const searchError = document.getElementById('searchError');
    const searchResults = document.getElementById('searchResults');
    
    // Mobile nav elements
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const mobileNavClose = document.getElementById('mobileNavClose');
    const sidebar = document.getElementById('sidebar');
    const mobileNavLinks = document.querySelectorAll('.nav-link[data-mobile-close="true"]');
    
    // Modal elements
    const fileDetailsModal = new bootstrap.Modal(document.getElementById('fileDetailsModal'));
    const searchTipsModal = new bootstrap.Modal(document.getElementById('searchTipsModal'));
    const modalFilename = document.getElementById('modalFilename');
    const modalFilesize = document.getElementById('modalFilesize');
    const modalDownloadLink = document.getElementById('modalDownloadLink');
    const linkToCopy = document.getElementById('linkToCopy');
    const copyLinkBtn = document.getElementById('copyLinkBtn');
    const fileDetailsLoader = document.getElementById('fileDetailsLoader');
    const fileDetailsContent = document.getElementById('fileDetailsContent');
    const searchTipsBtn = document.getElementById('searchTipsBtn');
    
    // Variable to store current download link
    let currentDownloadLink = '';
    
    // Event Listeners
    searchBtn.addEventListener('click', handleSearch);
    searchQueryInput.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            handleSearch();
        }
    });
    
    // Copy link button
    copyLinkBtn.addEventListener('click', function() {
        linkToCopy.select();
        document.execCommand('copy');
        
        // Show tooltip feedback
        this.innerHTML = '<i class="bi bi-check2"></i>';
        this.style.backgroundColor = 'var(--neon-green)';
        
        setTimeout(() => {
            this.innerHTML = '<i class="bi bi-clipboard"></i>';
            this.style.backgroundColor = 'var(--neon-blue)';
        }, 2000);
    });
    
    // Search Tips Button
    searchTipsBtn.addEventListener('click', function() {
        searchTipsModal.show();
    });
    
    // Trending Search Items
    document.querySelectorAll('.trending-search-item').forEach(item => {
        item.addEventListener('click', function() {
            const searchText = this.textContent.trim();
            searchQueryInput.value = searchText;
            handleSearch();
            
            // Close modal if clicked from modal
            if (this.closest('#searchTipsModal')) {
                searchTipsModal.hide();
            }
        });
    });
    
    // Focus search input on page load
    searchQueryInput.focus();
    
    // Add animation effects for cyberpunk UI
    addUIEffects();
    
    // Mobile navigation functionality with overlay
    const menuOverlay = document.getElementById('menuOverlay');
    
    if (mobileNavToggle && mobileNavClose && sidebar && menuOverlay) {
        // Show mobile nav and overlay
        mobileNavToggle.addEventListener('click', function() {
            sidebar.classList.add('mobile-visible');
            menuOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling when menu is open
        });
        
        // Hide mobile nav and overlay
        function closeMenu() {
            sidebar.classList.remove('mobile-visible');
            menuOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Re-enable scrolling
        }
        
        // Close on X button click
        mobileNavClose.addEventListener('click', closeMenu);
        
        // Close on overlay click
        menuOverlay.addEventListener('click', closeMenu);
        
        // Handle nav links that should close menu on click
        mobileNavLinks.forEach(link => {
            link.addEventListener('click', closeMenu);
        });
    }
    
    // Mobile search button
    const mobileSearchBtn = document.getElementById('mobileSearchBtn');
    if (mobileSearchBtn) {
        mobileSearchBtn.addEventListener('click', function() {
            // Scroll to search section
            document.getElementById('search-section').scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            
            // Focus the search input
            setTimeout(() => {
                searchQueryInput.focus();
            }, 500);
        });
    }
    
    // Scroll to section function for navigation
    window.scrollToSection = function(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.scrollIntoView({ behavior: 'smooth' });
            
            // Close mobile nav menu if it's open
            if (sidebar && sidebar.classList.contains('mobile-visible')) {
                // Use the closeMenu function if available, or close manually
                if (typeof closeMenu === 'function') {
                    closeMenu();
                } else {
                    sidebar.classList.remove('mobile-visible');
                    if (menuOverlay) menuOverlay.classList.remove('active');
                    document.body.style.overflow = '';
                }
            }
            
            // Update active state in bottom navigation
            updateBottomNavigation(sectionId);
        }
    };
    
    // Function to update active state in bottom navigation
    function updateBottomNavigation(activeSectionId) {
        const bottomNavItems = document.querySelectorAll('.bottom-nav .nav-item');
        if (!bottomNavItems.length) return;
        
        // Remove active class from all items
        bottomNavItems.forEach(item => item.classList.remove('active'));
        
        // Add active class based on section ID
        let activeNavItem;
        
        switch(activeSectionId) {
            case 'search-section':
                activeNavItem = document.querySelector('.bottom-nav .nav-item:nth-child(2)');
                break;
            case 'results-section':
                activeNavItem = document.querySelector('.bottom-nav .nav-item:nth-child(3)');
                break;
            default:
                activeNavItem = document.querySelector('.bottom-nav .nav-item:nth-child(1)'); // Home
        }
        
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
    }
    
    // Update bottom navigation on scroll
    window.addEventListener('scroll', function() {
        const scrollPosition = window.scrollY;
        const searchSection = document.getElementById('search-section');
        const resultsSection = document.getElementById('results-section');
        
        if (!searchSection || !resultsSection) return;
        
        // Determine which section is currently in view
        if (scrollPosition < searchSection.offsetTop - 100) {
            updateBottomNavigation('home');
        } else if (scrollPosition < resultsSection.offsetTop - 100) {
            updateBottomNavigation('search-section');
        } else {
            updateBottomNavigation('results-section');
        }
    });
    
    // Handler Functions
    function handleSearch() {
        const query = searchQueryInput.value.trim();
        
        if (!query) {
            showError(searchError, 'Please enter a search term');
            return;
        }
        
        // Reset UI
        resetUI();
        
        // Show loading
        searchLoading.classList.remove('d-none');
        
        // Fetch search results
        fetch(`/api/search?search=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide loading
                searchLoading.classList.add('d-none');
                
                // Display results
                displayResults(data);
                
                // Scroll to results section
                document.getElementById('results-section').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            })
            .catch(error => {
                // Hide loading
                searchLoading.classList.add('d-none');
                
                // Show error
                showError(searchError, `Failed to fetch search results: ${error.message}`);
            });
    }
    
    function handleFileSelect(fileId, fileName) {
        // Reset modal state
        resetModal();
        
        // Open the modal with loading state
        fileDetailsModal.show();
        
        // Show loader, hide content
        fileDetailsLoader.classList.remove('d-none');
        fileDetailsContent.classList.add('d-none');
        
        // Fetch file details
        fetch(`/api/download?id=${encodeURIComponent(fileId)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide loader
                fileDetailsLoader.classList.add('d-none');
                fileDetailsContent.classList.remove('d-none');
                
                // Update modal content
                modalFilename.textContent = data.filename || fileName;
                modalFilesize.textContent = data.size || 'Unknown';
                
                if (data.downloadLink) {
                    currentDownloadLink = data.downloadLink;
                    modalDownloadLink.href = data.downloadLink;
                    linkToCopy.value = data.downloadLink;
                    modalDownloadLink.classList.remove('disabled');
                } else {
                    modalDownloadLink.href = '#';
                    linkToCopy.value = '';
                    modalDownloadLink.classList.add('disabled');
                }
            })
            .catch(error => {
                // Hide loader
                fileDetailsLoader.classList.add('d-none');
                
                // Show error in modal
                const modalFileError = document.getElementById('modalFileError');
                showError(modalFileError, `Failed to fetch file details: ${error.message}`);
            });
    }
    
    function resetModal() {
        // Reset other elements
        modalFilename.textContent = '...';
        modalFilesize.textContent = '...';
        modalDownloadLink.href = '#';
        linkToCopy.value = '';
        document.getElementById('modalFileError').classList.add('d-none');
        
        // Reset loaders
        fileDetailsLoader.classList.add('d-none');
        fileDetailsContent.classList.add('d-none');
    }
    
    // Function removed as per requirements
    
    function isVideoFile(filename) {
        if (!filename) return false;
        const ext = getFileExtension(filename);
        const videoExts = ['mp4', 'webm', 'ogv', 'mkv', 'avi', 'mov', 'wmv', 'm4v', 'mpg', 'mpeg'];
        return videoExts.includes(ext);
    }
    
    // Helper Functions
    function showError(element, message) {
        // Find the error message span inside the element
        const errorSpan = element.querySelector('.error-message') || element;
        errorSpan.textContent = message;
        
        element.classList.remove('d-none');
        
        // Auto hide after delay
        setTimeout(() => {
            element.classList.add('d-none');
        }, 5000);
    }
    
    function resetUI() {
        // Reset search section
        searchError.classList.add('d-none');
        
        // Remove active state from cards
        document.querySelectorAll('.card-file').forEach(card => {
            card.classList.remove('active');
        });
    }
    
    function displayResults(data) {
        searchResults.innerHTML = '';
        
        if (!data || data.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'text-center py-5';
            noResults.innerHTML = `
                <i class="bi bi-search display-1" style="color: rgba(255,255,255,0.1);"></i>
                <p class="mt-3 text-muted">No results found. Try a different search term.</p>
            `;
            searchResults.appendChild(noResults);
            return;
        }
        
        // Create results info
        const resultsInfo = document.createElement('div');
        resultsInfo.className = 'mb-4';
        resultsInfo.innerHTML = `
            <div class="card" style="background-color: rgba(0,204,255,0.05); border: 1px solid var(--neon-blue);">
                <div class="card-body d-flex align-items-center">
                    <i class="bi bi-info-circle me-3" style="color: var(--neon-blue); font-size: 1.5rem;"></i>
                    <p class="mb-0">
                        Found <strong>${data.length}</strong> results. Click on a file to view download details.
                    </p>
                </div>
            </div>
        `;
        searchResults.appendChild(resultsInfo);
        
        // Create a container for the cards
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'row g-4 results-container search-results-grid';
        
        // Create a card for each result
        data.forEach(result => {
            const col = document.createElement('div');
            col.className = 'col-md-3 col-lg-4 mb-4';
            
            const fileExt = getFileExtension(result.name);
            const fileIcon = getFileIcon(fileExt);
            
            const card = document.createElement('div');
            card.className = 'card-file';
            card.addEventListener('click', () => {
                // Remove active class from all cards
                document.querySelectorAll('.card-file').forEach(c => {
                    c.classList.remove('active');
                });
                
                // Add active class to this card
                card.classList.add('active');
                
                // Handle file selection
                handleFileSelect(result.link, result.name);
            });
            
            // Create the size badge with appropriate color based on file size
            const sizeClass = getSizeClass(result.size);
            
            card.innerHTML = `
                <div class="p-3 pb-2">
                    <div class="d-flex align-items-start mb-3">
                        <div class="file-property-icon me-3">
                            <i class="${fileIcon}"></i>
                        </div>
                        <div class="flex-grow-1">
                            <h5 class="text-truncate-2 mb-1" style="font-size: 0.95rem; font-weight: 500;">${result.name}</h5>
                            <span class="cyberpunk-badge">
                                <i class="bi bi-hdd me-1"></i> ${result.size}
                            </span>
                        </div>
                    </div>
                    <div class="d-flex justify-content-end">
                        <button class="btn btn-sm" style="background-color: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); color: var(--text-secondary);">
                            <i class="bi bi-arrow-right me-1"></i> Details
                        </button>
                    </div>
                </div>
            `;
            
            col.appendChild(card);
            resultsContainer.appendChild(col);
            
            // Add staggered animation for cards
            setTimeout(() => {
                card.classList.add('card-appear');
            }, 50 * resultsContainer.children.length);
        });
        
        searchResults.appendChild(resultsContainer);
    }
    
    function getSizeClass(sizeStr) {
        // Extract the size value and unit
        const match = sizeStr.match(/^([\d.]+)\s*([A-Za-z]+)$/);
        if (!match) return 'text-secondary';
        
        const value = parseFloat(match[1]);
        const unit = match[2].toUpperCase();
        
        if (unit === 'GB' && value > 10) return 'text-danger';
        if (unit === 'GB') return 'text-warning';
        return 'text-success';
    }
    
    function addUIEffects() {
        // Add hover events for links and buttons
        document.querySelectorAll('.nav-link, .search-btn, .download-btn').forEach(el => {
            el.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.transition = 'all 0.3s ease';
            });
            
            el.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
        
        // Add CSS for card animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes cardAppear {
                0% { opacity: 0; transform: translateY(20px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            
            .card-appear {
                animation: cardAppear 0.5s forwards;
            }
            
            @keyframes glowPulse {
                0% { box-shadow: 0 0 5px var(--neon-blue); }
                50% { box-shadow: 0 0 20px var(--neon-blue), 0 0 30px var(--neon-green); }
                100% { box-shadow: 0 0 5px var(--neon-blue); }
            }
            
            .glow-effect {
                animation: glowPulse 1.5s infinite;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Utility functions
    function getFileExtension(filename) {
        return filename.split('.').pop().toLowerCase();
    }
    
    function getFileIcon(ext) {
        const iconMap = {
            'mp4': 'bi bi-film',
            'avi': 'bi bi-film',
            'mkv': 'bi bi-film',
            'mov': 'bi bi-film',
            'wmv': 'bi bi-film',
            'mp3': 'bi bi-music-note-beamed',
            'wav': 'bi bi-music-note-beamed',
            'flac': 'bi bi-music-note-beamed',
            'pdf': 'bi bi-file-earmark-pdf',
            'doc': 'bi bi-file-earmark-word',
            'docx': 'bi bi-file-earmark-word',
            'xls': 'bi bi-file-earmark-excel',
            'xlsx': 'bi bi-file-earmark-excel',
            'ppt': 'bi bi-file-earmark-slides',
            'pptx': 'bi bi-file-earmark-slides',
            'zip': 'bi bi-file-earmark-zip',
            'rar': 'bi bi-file-earmark-zip',
            '7z': 'bi bi-file-earmark-zip',
            'jpg': 'bi bi-file-earmark-image',
            'jpeg': 'bi bi-file-earmark-image',
            'png': 'bi bi-file-earmark-image',
            'gif': 'bi bi-file-earmark-image',
            'exe': 'bi bi-file-earmark-binary',
            'iso': 'bi bi-disc',
            'torrent': 'bi bi-magnet'
        };
        
        return iconMap[ext] || 'bi bi-file-earmark';
    }
});