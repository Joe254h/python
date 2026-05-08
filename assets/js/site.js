(function() {
  const currentYear = document.querySelector('#currentYear');
  if (currentYear) {
    currentYear.textContent = new Date().getFullYear();
  }

  const copyButton = document.querySelector('#copyEmail');
  const copyStatus = document.querySelector('#copyStatus');
  const email = 'sangura.j.nyongesa@aims-senegal.org';

  if (copyButton && copyStatus && navigator.clipboard) {
    copyButton.addEventListener('click', async () => {
      await navigator.clipboard.writeText(email);
      copyStatus.textContent = 'Email copied to clipboard.';
      setTimeout(() => {
        copyStatus.textContent = '';
      }, 2500);
    });
  }
})();
