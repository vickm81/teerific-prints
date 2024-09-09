barba.init({
    cacheFirstPage: true,
    cacheIgnore: false,
    debug: false,
    logLevel: 'off',
    prefetchIgnore: false,
    prevent: null,
    preventRunning: false,
    schema: [[SchemaAttribute]],
    timeout: 2e3,
    transitions: [],
    views: [],
  })

// Smooth hover effect for WhatsApp button (Optional)
document.querySelector('.whatsapp-float').addEventListener('mouseover', function() {
    this.style.transform = 'scale(1.1)';
});

document.querySelector('.whatsapp-float').addEventListener('mouseout', function() {
    this.style.transform = 'scale(1)';
});



