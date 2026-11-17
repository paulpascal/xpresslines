import { toPng } from 'html-to-image';
import { useRef, useState } from 'react';

/** Save an element (the ticket) as a PNG, leaving out anything marked data-no-export. */
export function useTicketDownload(fileName: string) {
  const ref = useRef<HTMLDivElement>(null);
  const [downloading, setDownloading] = useState(false);

  async function download() {
    if (!ref.current) return;
    setDownloading(true);
    try {
      const png = await toPng(ref.current, {
        backgroundColor: 'white',
        pixelRatio: 2,
        filter: (node) => !(node instanceof HTMLElement && node.dataset.noExport !== undefined),
      });
      const link = document.createElement('a');
      link.href = png;
      link.download = fileName;
      link.click();
    } finally {
      setDownloading(false);
    }
  }

  return { ref, download, downloading };
}
