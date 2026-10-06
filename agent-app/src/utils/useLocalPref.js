import { useState, useEffect } from 'react';
import { getPref } from '../data/localPrefs';

export default function useLocalPref(key) {
  const [value, setValue] = useState(() => getPref(key));
  useEffect(() => {
    const update = () => setValue(getPref(key));
    window.addEventListener('phiagent-prefs-changed', update);
    window.addEventListener('storage', update);
    return () => { window.removeEventListener('phiagent-prefs-changed', update); window.removeEventListener('storage', update); };
  }, [key]);
  return value;
}
