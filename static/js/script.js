document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const searchQueryInput = document.getElementById('searchQuery');
    const searchBtn = document.getElementById('searchBtn');
    const searchLoading = document.getElementById('searchLoading');
    const searchError = document.getElementById('searchError');
    const searchResults = document.getElementById('searchResults');
    
    // Filter and Sort elements
    const filterOptions = document.querySelectorAll('.filter-option');
    const sortOptions = document.querySelectorAll('.sort-option');
    
    // Mobile nav elements
    const mobileNavToggle = document.getElementById('mobileNavToggle');
    const mobileNavClose = document.getElementById('mobileNavClose');
    const sidebar = document.getElementById('sidebar');
    const mobileNavLinks = document.querySelectorAll('.nav-link[data-mobile-close="true"]');
    
    // Modal elements (using Bootstrap)
    const fileDetailsModal = new bootstrap.Modal(document.getElementById('fileDetailsModal'), {
        backdrop: 'static'
    });
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
    
    // Filter options click handlers
    filterOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const filterType = this.getAttribute('data-filter');
            applyFilter(filterType);
        });
    });
    
    // Sort options click handlers
    sortOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const sortType = this.getAttribute('data-sort');
            applySort(sortType);
        });
    });
    
    // Copy link button
    if (copyLinkBtn) {
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
    }
    
    // Search Tips Button
    if (searchTipsBtn) {
        searchTipsBtn.addEventListener('click', function() {
            searchTipsModal.show();
        });
    }
    
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
    if (searchQueryInput) {
        searchQueryInput.focus();
    }
    
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
        
        // Scroll to results section immediately
        document.getElementById('results-section').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
        
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
            })
            .catch(error => {
                // Hide loading
                searchLoading.classList.add('d-none');
                
                // Show error
                showError(searchError, `Failed to fetch search results: ${error.message}`);
            });
    }
    
    function handleFileSelect(fileId, fileName, fileSize, autoDownload = false) {
        // Reset modal state
        resetModal();
        
        // Update immediately with what we know
        if (fileName) {
            document.querySelector('#modalFilename').textContent = fileName;
        }
        
        if (fileSize) {
            document.querySelector('#modalFilesize').textContent = fileSize;
        }
        
        // If auto-download is requested, skip showing the modal
        if (!autoDownload) {
            // Open the modal with loading state
            fileDetailsModal.show();
            
            // Show loader, hide content
            fileDetailsLoader.classList.remove('d-none');
            fileDetailsContent.classList.add('d-none');
        }
        
        // Fetch file details
        fetch(`/api/download?id=${encodeURIComponent(fileId)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Update modal content with full info from server if modal is shown
                if (!autoDownload) {
                    // Hide loader
                    fileDetailsLoader.classList.add('d-none');
                    fileDetailsContent.classList.remove('d-none');
                    
                    if (data.filename && data.filename !== "Unknown") {
                        document.querySelector('#modalFilename').textContent = data.filename;
                    }
                    
                    if (data.size && data.size !== "Unknown size") {
                        document.querySelector('#modalFilesize').textContent = data.size;
                    }
                }
                
                // Set download link
                if (data.downloadLink) {
                    // Save current link
                    currentDownloadLink = data.downloadLink;
                    
                    // Update modal elements if showing the modal
                    if (!autoDownload) {
                        // Update download button
                        const downloadBtn = document.querySelector('#modalDownloadLink');
                        if (downloadBtn) {
                            downloadBtn.href = data.downloadLink;
                            downloadBtn.classList.remove('disabled');
                            
                            // Add pulsing effect
                            downloadBtn.classList.add('pulse-animation');
                            setTimeout(() => {
                                downloadBtn.classList.remove('pulse-animation');
                            }, 2000);
                        }
                        
                        // Update link input field
                        const linkInput = document.querySelector('#linkToCopy');
                        if (linkInput) {
                            linkInput.value = data.downloadLink;
                        }
                        
                        // Show ready status
                        document.querySelector('.file-status-badge').textContent = 'Ready for download';
                    }
                    
                    // If auto-download is requested, trigger the download
                    if (autoDownload && data.downloadLink) {
                        window.location.href = data.downloadLink;
                    }
                } else {
                    // Handle no download link case
                    if (!autoDownload) {
                        document.querySelector('#modalDownloadLink').href = '#';
                        document.querySelector('#modalDownloadLink').classList.add('disabled');
                        document.querySelector('#linkToCopy').value = '';
                        
                        // Show not ready status
                        document.querySelector('.file-status-badge').textContent = 'Download unavailable';
                    }
                }
            })
            .catch(error => {
                if (!autoDownload) {
                    // Hide loader but keep some content visible
                    fileDetailsLoader.classList.add('d-none');
                    fileDetailsContent.classList.remove('d-none');
                    
                    // Update status to show error
                    document.querySelector('.file-status-badge').textContent = 'Error loading file';
                    
                    // Show error in modal
                    const modalFileError = document.getElementById('modalFileError');
                    showError(modalFileError, `Failed to fetch file details: ${error.message}`);
                } else {
                    // Show a toast or notification for auto-download failure
                    alert(`Failed to download file: ${error.message}`);
                }
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
    
    function getFileTypeIcon(fileName) {
        if (!fileName) return 'bi-file-earmark';
        
        const ext = getFileExtension(fileName).toLowerCase();
        
        // Video files
        if (['mp4', 'webm', 'mkv', 'avi', 'mov', 'wmv', 'm4v'].includes(ext)) {
            return 'bi-film';
        }
        
        // Audio files
        if (['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext)) {
            return 'bi-music-note-beamed';
        }
        
        // Image files
        if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
            return 'bi-image';
        }
        
        // Document files
        if (['pdf', 'doc', 'docx', 'txt', 'rtf'].includes(ext)) {
            return 'bi-file-earmark-text';
        }
        
        // Archive files
        if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
            return 'bi-file-earmark-zip';
        }
        
        // Executable files
        if (['exe', 'msi', 'dmg', 'app'].includes(ext)) {
            return 'bi-file-earmark-code';
        }
        
        return 'bi-file-earmark';
    }
    
    function getFileExtension(fileName) {
        if (!fileName) return '';
        return fileName.split('.').pop() || '';
    }
    
    function isVideoFile(fileName) {
        if (!fileName) return false;
        const ext = getFileExtension(fileName).toLowerCase();
        const videoExts = ['mp4', 'webm', 'ogv', 'mkv', 'avi', 'mov', 'wmv', 'm4v', 'mpg', 'mpeg'];
        return videoExts.includes(ext);
    }
    
    // Helper Functions
    function showError(element, message) {
        if (!element) return;
        
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
        if (searchError) searchError.classList.add('d-none');
        
        // Remove active state from cards
        document.querySelectorAll('.card-file').forEach(card => {
            card.classList.remove('active');
        });
    }
    
    function displayResults(data) {
        if (!searchResults) return;
        
        searchResults.innerHTML = '';
        
        // Store original results for filtering/sorting
        originalSearchResults = Array.isArray(data) ? [...data] : [];
        
        // Reset filter and sort buttons to default state
        document.querySelector('#filterBtn').innerHTML = '<i class="bi bi-filter"></i>';
        document.querySelector('#sortBtn').innerHTML = '<i class="bi bi-arrow-down-up"></i>';
        
        if (!data || data.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'text-center py-5';
            noResults.innerHTML = `
                <div style="width: 80px; height: 80px; margin: 0 auto; border-radius: 50%; background: rgba(53, 239, 255, 0.05); display: flex; justify-content: center; align-items: center; border: 1px solid rgba(53, 239, 255, 0.1);">
                    <i class="bi bi-search" style="font-size: 2rem; color: var(--neon-blue);"></i>
                </div>
                <p class="mt-4 text-muted">No results found. Try another search term.</p>
                <p class="small text-muted">Try using different keywords or check your spelling</p>
            `;
            searchResults.appendChild(noResults);
            return;
        }
        
        // Create row for grid layout
        const row = document.createElement('div');
        row.className = 'row g-3';
        
        // Add each file as a card
        data.forEach(file => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4';
            
            const fileIcon = getFileTypeIcon(file.name);
            const fileIconColor = isVideoFile(file.name) ? 'var(--neon-blue)' : 'var(--neon-green)';
            
            col.innerHTML = `
                <div class="card-file" data-id="${file.link}" data-name="${file.name}" data-size="${file.size}">
                    <div class="card-file-icon">
                        <i class="bi ${fileIcon} fs-4" style="color: var(--neon-blue);"></i>
                    </div>
                    <div class="card-file-info">
                        <div class="card-file-name">${file.name}</div>
                        <div class="file-meta">
                            <div class="card-file-size">${file.size}</div>
                            <div class="file-type">${getFileExtension(file.name).toUpperCase()}</div>
                        </div>
                    </div>
                    <div class="file-actions">
                        <a href="#" class="file-action-btn">
                            <i class="bi bi-cloud-download"></i>
                        </a>
                        <a href="#" class="file-action-btn">
                            <i class="bi bi-info-circle"></i>
                        </a>
                    </div>
                </div>
            `;
            
            const cardFile = col.querySelector('.card-file');
            
            // Add click event to the file card
            cardFile.addEventListener('click', function(e) {
                // If clicking on an action button, don't trigger the card click
                if (e.target.closest('.file-action-btn')) return;
                
                // Get data attributes
                const fileId = this.getAttribute('data-id');
                const fileName = this.getAttribute('data-name');
                const fileSize = this.getAttribute('data-size');
                
                // Mark this card as active
                document.querySelectorAll('.card-file').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                
                // Handle file selection
                handleFileSelect(fileId, fileName, fileSize);
            });
            
            // Add click events to the action buttons
            const downloadBtn = cardFile.querySelector('.file-action-btn:first-child');
            const infoBtn = cardFile.querySelector('.file-action-btn:last-child');
            
            downloadBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Prevent card click
                
                const fileId = cardFile.getAttribute('data-id');
                const fileName = cardFile.getAttribute('data-name');
                const fileSize = cardFile.getAttribute('data-size');
                
                handleFileSelect(fileId, fileName, fileSize, true); // Set last param to true to auto-download
            });
            
            infoBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Prevent card click
                
                const fileId = cardFile.getAttribute('data-id');
                const fileName = cardFile.getAttribute('data-name');
                const fileSize = cardFile.getAttribute('data-size');
                
                handleFileSelect(fileId, fileName, fileSize);
            });
            
            row.appendChild(col);
        });
        
        searchResults.appendChild(row);
    }
    
    function addUIEffects() {
        // Add hover effect to buttons
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                if (!this.classList.contains('search-btn')) return;
                this.style.transform = 'translateY(-2px)';
            });
            button.addEventListener('mouseleave', function() {
                if (!this.classList.contains('search-btn')) return;
                this.style.transform = '';
            });
        });
        
        // Add particles or other visual effects if needed
    }
    
    // Filter and sort functions
    
    // Store the original search results for filtering/sorting
    let originalSearchResults = [];
    
    // Apply filter to search results
    function applyFilter(filterType) {
        // If no results yet, return
        if (originalSearchResults.length === 0) return;
        
        // Clone the original results to work with
        let filteredResults = [...originalSearchResults];
        
        // Apply the filter
        switch(filterType) {
            case 'video':
                filteredResults = originalSearchResults.filter(file => {
                    const ext = getFileExtension(file.name).toLowerCase();
                    return ['mp4', 'webm', 'mkv', 'avi', 'mov', 'wmv', 'm4v'].includes(ext);
                });
                break;
            case 'audio':
                filteredResults = originalSearchResults.filter(file => {
                    const ext = getFileExtension(file.name).toLowerCase();
                    return ['mp3', 'wav', 'ogg', 'flac', 'm4a'].includes(ext);
                });
                break;
                case 'large':
                    filteredResults = originalSearchResults.filter(file => {
                        // Assuming file size is stored as "XX.XX GB", "XXX.XX MB", etc.
                        const sizeStr = file.size.toLowerCase();
                        // Check if size is greater than 5GB
                        if (sizeStr.includes('gb')) {
                            const sizeNum = parseFloat(sizeStr);
                            return sizeNum > 5;
                        }
                        // Check if size is over 5000 MB
                        if (sizeStr.includes('mb')) {
                            const sizeNum = parseFloat(sizeStr);
                            return sizeNum > 5000;
                        }
                        return false;
                    });
                    break;
                case 'medium':
                    filteredResults = originalSearchResults.filter(file => {
                        // Assuming file size is stored as "XX.XX GB", "XXX.XX MB", etc.
                        const sizeStr = file.size.toLowerCase();
                        // Check if size is between 1GB and 5GB
                        if (sizeStr.includes('gb')) {
                            const sizeNum = parseFloat(sizeStr);
                            return sizeNum >= 1 && sizeNum <= 5;
                        }
                        // Check if size is between 1000 MB and 5000 MB
                        if (sizeStr.includes('mb')) {
                            const sizeNum = parseFloat(sizeStr);
                            return sizeNum >= 1000 && sizeNum <= 5000;
                        }
                        return false;
                    });
                    break;
                case 'small':
                    filteredResults = originalSearchResults.filter(file => {
                        // Assuming file size is stored as "XX.XX GB", "XXX.XX MB", etc.
                        const sizeStr = file.size.toLowerCase();
                        // Check if size is in KB range
                        if (sizeStr.includes('kb')) {
                            return true;
                        }
                        // Check if size is less than 1GB (1000 MB)
                        if (sizeStr.includes('mb')) {
                            return true;
                        }
                        // Check if size is less than 1GB
                        if (sizeStr.includes('gb')) {
                            const sizeNum = parseFloat(sizeStr);
                            return sizeNum < 1;
                        }
                        return false;
                    });
                    break;
            case 'all':
            default:
                // No filter
                break;
        }
        
        // Update the display with filtered results
        updateResultsDisplay(filteredResults);
        
        // Update the filter button UI
        document.querySelector('#searchResultCount').innerHTML = `<i class="bi bi-filter"></i><span class="d-none d-md-inline">${filteredResults.length} items</span>`;
    }
    
    // Apply sorting to search results
    function applySort(sortType) {
        // If no results yet, return
        if (originalSearchResults.length === 0) return;
        
        // Clone the current results to work with
        let sortedResults = [...originalSearchResults];
        
        // Apply the sort
        switch(sortType) {
            case 'name-asc':
                sortedResults.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'name-desc':
                sortedResults.sort((a, b) => b.name.localeCompare(a.name));
                break;
            case 'size-asc':
                // Sort by size (smallest first), need to convert size string to comparable value
                sortedResults.sort((a, b) => {
                    const sizeA = convertSizeToBytes(a.size);
                    const sizeB = convertSizeToBytes(b.size);
                    return sizeA - sizeB;
                });
                break;
            case 'size-desc':
                // Sort by size (largest first)
                sortedResults.sort((a, b) => {
                    const sizeA = convertSizeToBytes(a.size);
                    const sizeB = convertSizeToBytes(b.size);
                    return sizeB - sizeA;
                });
                break;
            default:
                // No sorting
                break;
        }
        
        // Update the display with sorted results
        updateResultsDisplay(sortedResults);
        
        // Update the sort button UI
        let sortLabel = 'Sort';
        switch(sortType) {
            case 'name-asc': sortLabel = 'A-Z'; break;
            case 'name-desc': sortLabel = 'Z-A'; break;
            case 'size-asc': sortLabel = 'Size ↑'; break;
            case 'size-desc': sortLabel = 'Size ↓'; break;
        }
        document.querySelector('#sortState').innerHTML = `<i class="bi bi-arrow-down-up"></i> <span class="d-none d-md-inline">${sortLabel}</span>`;
    }
    
    // Helper function to convert size string to bytes for sorting
    function convertSizeToBytes(sizeStr) {
        if (!sizeStr) return 0;
        sizeStr = sizeStr.toLowerCase();
        
        const value = parseFloat(sizeStr.replace(/[^\d.]/g, ''));
        
        if (sizeStr.includes('kb')) {
            return value * 1024;
        } else if (sizeStr.includes('mb')) {
            return value * 1024 * 1024;
        } else if (sizeStr.includes('gb')) {
            return value * 1024 * 1024 * 1024;
        } else if (sizeStr.includes('tb')) {
            return value * 1024 * 1024 * 1024 * 1024;
        }
        
        return value; // Bytes or unknown unit
    }
    
    // Update display with filtered/sorted results
    function updateResultsDisplay(results) {
        // Clear current results
        searchResults.innerHTML = '';
        
        // If no results after filtering
        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="text-center py-5">
                    <div style="width: 80px; height: 80px; margin: 0 auto; border-radius: 50%; background: rgba(53, 239, 255, 0.05); display: flex; justify-content: center; align-items: center; border: 1px solid rgba(53, 239, 255, 0.1);">
                        <i class="bi bi-filter" style="font-size: 2rem; color: var(--neon-blue);"></i>
                    </div>
                    <p class="mt-4 text-muted">No files match the current filter</p>
                    <button class="btn btn-sm mt-2" id="resetFilterBtn" style="background-color: var(--button-bg); border: var(--button-border);">
                        Reset Filter
                    </button>
                </p>
            `;
            
            // Add reset filter button handler
            document.getElementById('resetFilterBtn').addEventListener('click', function() {
                updateResultsDisplay(originalSearchResults);
                document.querySelector('#filterBtn').innerHTML = '<i class="bi bi-filter"></i>';
                document.querySelector('#sortBtn').innerHTML = '<i class="bi bi-arrow-down-up"></i>';
            });
            
            return;
        }
        
        // Create the results container
        const row = document.createElement('div');
        row.className = 'row g-3';
        
        // Add each result
        results.forEach(file => {
            // Create card components (similar to displayResults function)
            const col = document.createElement('div');
            col.className = 'col-sm-6 col-md-4 col-lg-3';
            
            // Get appropriate icon
            const fileIcon = getFileTypeIcon(file.name);
            const isVideo = isVideoFile(file.name);
            
            // Create card HTML
            col.innerHTML = `
                <div class="card card-file" data-id="${file.id}" data-name="${file.name}" data-size="${file.size}">
                    <div class="card-body">
                        <div class="file-icon"><i class="bi ${fileIcon}"></i></div>
                        <div class="file-name" title="${file.name}">${file.name}</div>
                        <div class="file-size">${file.size}</div>
                        <div class="file-actions">
                            <button class="btn btn-sm direct-download-btn">
                                <i class="bi bi-download"></i>
                            </button>
                            <button class="btn btn-sm file-info-btn">
                                <i class="bi bi-info-circle"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Get references
            const cardFile = col.querySelector('.card-file');
            const downloadBtn = col.querySelector('.direct-download-btn');
            const infoBtn = col.querySelector('.file-info-btn');
            
            // Add event listeners for the card
            cardFile.addEventListener('click', function() {
                const fileId = this.getAttribute('data-id');
                const fileName = this.getAttribute('data-name');
                const fileSize = this.getAttribute('data-size');
                
                handleFileSelect(fileId, fileName, fileSize);
            });
            
            // Add event listener for download button
            downloadBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Prevent card click
                
                const fileId = cardFile.getAttribute('data-id');
                const fileName = cardFile.getAttribute('data-name');
                const fileSize = cardFile.getAttribute('data-size');
                
                handleFileSelect(fileId, fileName, fileSize, true); // Auto-download
            });
            
            // Add event listener for info button
            infoBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation(); // Prevent card click
                
                const fileId = cardFile.getAttribute('data-id');
                const fileName = cardFile.getAttribute('data-name');
                const fileSize = cardFile.getAttribute('data-size');
                
                handleFileSelect(fileId, fileName, fileSize);
            });
            
            row.appendChild(col);
        });
        
        searchResults.appendChild(row);
    }
});