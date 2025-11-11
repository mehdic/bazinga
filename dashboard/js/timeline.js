// Timeline Visualization using D3.js
class TimelineViz {
    constructor() {
        this.container = document.getElementById('timeline-container');
        this.data = [];
    }

    async loadTimeline() {
        try {
            const response = await fetch('/api/timeline');
            const result = await response.json();
            this.data = result.timeline || [];
            this.render();
        } catch (error) {
            console.error('Failed to load timeline:', error);
        }
    }

    render() {
        if (!this.data || this.data.length === 0) {
            this.container.innerHTML = '<div class="placeholder"><p>No timeline data available yet...</p></div>';
            return;
        }

        // Clear container
        this.container.innerHTML = '';

        // Set up dimensions
        const margin = { top: 20, right: 30, bottom: 40, left: 120 };
        const width = this.container.clientWidth - margin.left - margin.right;
        const height = Math.max(400, this.data.length * 40);

        // Create SVG
        const svg = d3.select(this.container)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Parse timestamps
        const timeData = this.data.map(d => ({
            ...d,
            start: new Date(d.timestamp),
            end: new Date(d.timestamp + (d.duration || 0) * 1000)
        }));

        // Create scales
        const xScale = d3.scaleTime()
            .domain([
                d3.min(timeData, d => d.start),
                d3.max(timeData, d => d.end)
            ])
            .range([0, width]);

        const yScale = d3.scaleBand()
            .domain(timeData.map((d, i) => i))
            .range([0, height])
            .padding(0.2);

        // X axis
        svg.append('g')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale));

        // Timeline bars
        svg.selectAll('.timeline-bar')
            .data(timeData)
            .enter()
            .append('rect')
            .attr('class', d => `timeline-bar status-${d.status}`)
            .attr('x', d => xScale(d.start))
            .attr('y', (d, i) => yScale(i))
            .attr('width', d => Math.max(5, xScale(d.end) - xScale(d.start)))
            .attr('height', yScale.bandwidth())
            .attr('fill', d => this.getStatusColor(d.status))
            .attr('opacity', 0.8);

        // Labels
        svg.selectAll('.timeline-label')
            .data(timeData)
            .enter()
            .append('text')
            .attr('class', 'timeline-label')
            .attr('x', -10)
            .attr('y', (d, i) => yScale(i) + yScale.bandwidth() / 2)
            .attr('text-anchor', 'end')
            .attr('dominant-baseline', 'middle')
            .text(d => d.agent)
            .style('font-size', '12px')
            .style('fill', '#ffffff');

        // Action descriptions
        svg.selectAll('.timeline-action')
            .data(timeData)
            .enter()
            .append('text')
            .attr('class', 'timeline-action')
            .attr('x', d => xScale(d.start) + 5)
            .attr('y', (d, i) => yScale(i) + yScale.bandwidth() / 2)
            .attr('dominant-baseline', 'middle')
            .text(d => d.action)
            .style('font-size', '11px')
            .style('fill', '#ffffff');
    }

    getStatusColor(status) {
        const colors = {
            'completed': '#10b981',
            'in-progress': '#f59e0b',
            'pending': '#6b7280',
            'failed': '#ef4444'
        };
        return colors[status] || '#6b7280';
    }
}

// Initialize
window.timelineViz = new TimelineViz();
