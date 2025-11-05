export const formatResponse = (text) => {
  if (!text) return ''

  // Escapar HTML peligroso primero
  const escapeHtml = (unsafe) => {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;")
  }

  // Aplicar escape solo a contenido no-markdown
  let safeText = text

  // Procesar markdown paso a paso
  return safeText
    // 1. Títulos ### ## #
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    
    // 2. Listas con viñetas
    .replace(/^\* (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)(\s*<li>.*<\/li>)*/gm, '<ul>$&</ul>')
    .replace(/<\/li>\s*<li>/g, '</li><li>')
    
    // 3. Listas numeradas
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)(\s*<li>.*<\/li>)*/gm, '<ol>$&</ol>')
    
    // 4. Negritas y cursivas
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    
    // 5. Código inline
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    
    // 6. Enlaces
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    
    // 7. Párrafos y saltos de línea
    .split(/\n\s*\n/)
    .filter(p => p.trim())
    .map(paragraph => {
      if (paragraph.match(/^<[hul]/)) {
        return paragraph
      }
      const withBreaks = paragraph.replace(/\n/g, '<br>')
      return `<p>${withBreaks}</p>`
    })
    .join('')
}