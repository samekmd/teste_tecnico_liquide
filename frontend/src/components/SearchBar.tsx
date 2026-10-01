import styles from './SearchBar.module.css';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className={styles.search}>
      <label htmlFor="search">Buscar produtos</label>
      <input
        id="search"
        type="search"
        value={value}
        placeholder="Título, EAN ou categoria"
        autoComplete="off"
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
