// Extract all tables from the page as structured data
(function() {
    function tableToArray(table) {
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
        const rows = Array.from(table.querySelectorAll('tbody tr, tr')).filter(tr => !tr.querySelector('th'));

        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            if (headers.length > 0) {
                // Use headers as keys
                const obj = {};
                cells.forEach((cell, i) => {
                    obj[headers[i] || `column_${i}`] = cell.textContent.trim();
                });
                return obj;
            } else {
                // No headers, just return array
                return cells.map(cell => cell.textContent.trim());
            }
        });
    }

    const tables = Array.from(document.querySelectorAll('table'));

    if (tables.length === 0) {
        return { error: 'No tables found on this page' };
    }

    return tables.map((table, index) => ({
        index,
        rows: table.rows.length,
        columns: table.rows[0]?.cells.length || 0,
        data: tableToArray(table)
    }));
})()
