'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

interface MultiSelectProps {
    label: string;
    options: number[];
    selected: number[];
    onChange: (selected: number[]) => void;
}

export default function MultiSelect({ label, options, selected, onChange }: MultiSelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [dropdownRef]);

    const toggleOption = (option: number) => {
        if (selected.includes(option)) {
            onChange(selected.filter(item => item !== option));
        } else {
            // Sort selected years to keep them ordered
            onChange([...selected, option].sort((a, b) => b - a));
        }
    };

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg transition-colors border border-white/20"
            >
                <span className="text-sm font-medium">{label}</span>
                {selected.length > 0 && (
                    <span className="bg-purple-600 text-xs px-2 py-0.5 rounded-full">
                        {selected.length}
                    </span>
                )}
                <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-slate-800 border border-white/20 rounded-xl shadow-2xl z-50 overflow-hidden">
                    <div className="p-2 space-y-1">
                        {options.map((option) => (
                            <button
                                key={option}
                                onClick={() => toggleOption(option)}
                                className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-200 hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <span>{option}</span>
                                {selected.includes(option) && (
                                    <Check className="w-4 h-4 text-emerald-400" />
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
