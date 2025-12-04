---
name: tailwind
type: framework
priority: 2
token_estimate: 350
compatible_with: [developer, senior_software_engineer]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Tailwind CSS Engineering Expertise

## Specialist Profile
Tailwind specialist building consistent, responsive UIs. Expert in utility-first CSS, component patterns, and design systems.

## Implementation Guidelines

### Component Patterns

```tsx
// Button with variants
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

const variants = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800',
  danger: 'bg-red-600 hover:bg-red-700 text-white',
};

const sizes = {
  sm: 'px-2 py-1 text-sm',
  md: 'px-4 py-2',
  lg: 'px-6 py-3 text-lg',
};

export function Button({ variant = 'primary', size = 'md', children }: ButtonProps) {
  return (
    <button className={`
      ${variants[variant]}
      ${sizes[size]}
      rounded-md font-medium transition-colors
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed
    `}>
      {children}
    </button>
  );
}
```

### Responsive Design

```tsx
<div className="
  grid gap-4
  grid-cols-1
  sm:grid-cols-2
  lg:grid-cols-3
  xl:grid-cols-4
">
  {items.map(item => (
    <Card key={item.id} item={item} />
  ))}
</div>

// Mobile-first responsive text
<h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl">
  Responsive Heading
</h1>
```

### Dark Mode

```tsx
<div className="
  bg-white dark:bg-gray-900
  text-gray-900 dark:text-gray-100
  border border-gray-200 dark:border-gray-700
">
  <h2 className="text-gray-800 dark:text-gray-200">Title</h2>
  <p className="text-gray-600 dark:text-gray-400">Description</p>
</div>
```

### Custom Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          500: '#0ea5e9',
          900: '#0c4a6e',
        },
      },
      spacing: {
        '18': '4.5rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### Class Organization

```tsx
// Order: layout → sizing → spacing → typography → colors → effects
<div className="
  flex flex-col          /* layout */
  w-full max-w-md        /* sizing */
  p-4 space-y-2          /* spacing */
  text-sm font-medium    /* typography */
  bg-white text-gray-900 /* colors */
  rounded-lg shadow-md   /* effects */
">
```

## Patterns to Avoid
- ❌ Arbitrary values when tokens exist
- ❌ Overriding with !important
- ❌ Mixing Tailwind with custom CSS
- ❌ Inconsistent spacing values

## Verification Checklist
- [ ] Mobile-first responsive
- [ ] Dark mode support
- [ ] Consistent spacing scale
- [ ] Accessible color contrast
- [ ] Reusable component patterns
