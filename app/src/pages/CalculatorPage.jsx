import { useState } from 'react';
import Icon from '../components/Icon';
import './CalculatorPage.css';

const CalculatorPage = () => {
  const [display, setDisplay] = useState('0');
  const [prevValue, setPrevValue] = useState(null);
  const [operator, setOperator] = useState(null);
  const [waitingForOperand, setWaitingForOperand] = useState(false);
  const [history, setHistory] = useState([]);
  const [mode, setMode] = useState('standard');
  const [showHistory, setShowHistory] = useState(false);

  const inputDigit = (digit) => {
    if (waitingForOperand) {
      setDisplay(String(digit));
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? String(digit) : display + digit);
    }
  };

  const inputDecimal = () => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
      return;
    }
    if (!display.includes('.')) {
      setDisplay(display + '.');
    }
  };

  const clearAll = () => {
    setDisplay('0');
    setPrevValue(null);
    setOperator(null);
    setWaitingForOperand(false);
  };

  const clearEntry = () => {
    setDisplay('0');
  };

  const backspace = () => {
    if (display.length === 1 || (display.length === 2 && display.startsWith('-'))) {
      setDisplay('0');
    } else {
      setDisplay(display.slice(0, -1));
    }
  };

  const toggleSign = () => {
    setDisplay(String(-parseFloat(display)));
  };

  const addToHistory = (expression, result) => {
    setHistory(prev => [{ expression, result, time: new Date().toLocaleTimeString() }, ...prev.slice(0, 49)]);
  };

  const calculate = (a, b, op) => {
    const numA = parseFloat(a);
    const numB = parseFloat(b);
    let result;
    let expression = `${a} ${op} ${b}`;

    switch (op) {
      case '+':
        result = numA + numB;
        break;
      case '-':
        result = numA - numB;
        break;
      case '×':
        result = numA * numB;
        break;
      case '÷':
        if (numB === 0) {
          return { error: '除数不能为零' };
        }
        result = numA / numB;
        break;
      case '^':
        if (numA === 0 && numB === 0) {
          return { error: '0的0次方无意义' };
        }
        result = Math.pow(numA, numB);
        break;
      case 'mod':
        result = numA % numB;
        break;
      case 'gcd':
        result = gcd(Math.abs(Math.floor(numA)), Math.abs(Math.floor(numB)));
        expression = `gcd(${numA}, ${numB})`;
        break;
      case 'lcm':
        result = lcm(Math.abs(Math.floor(numA)), Math.abs(Math.floor(numB)));
        expression = `lcm(${numA}, ${numB})`;
        break;
      case 'avg':
        result = (numA + numB) / 2;
        expression = `avg(${numA}, ${numB})`;
        break;
      default:
        result = numB;
    }

    return { result: formatResult(result), expression };
  };

  const gcd = (a, b) => {
    if (b === 0) return a;
    return gcd(b, a % b);
  };

  const lcm = (a, b) => {
    if (a === 0 || b === 0) return 0;
    return (a * b) / gcd(a, b);
  };

  const formatResult = (num) => {
    if (isNaN(num)) return '错误';
    if (!isFinite(num)) return '无穷大';
    const str = Number(num.toPrecision(12)).toString();
    return str;
  };

  const performOperation = (nextOperator) => {
    const inputValue = display;

    if (prevValue === null) {
      setPrevValue(inputValue);
    } else if (operator) {
      const result = calculate(prevValue, inputValue, operator);
      if (result.error) {
        setDisplay(result.error);
        setPrevValue(null);
        setOperator(null);
        setWaitingForOperand(true);
        return;
      }
      setDisplay(result.result);
      setPrevValue(result.result);
      addToHistory(result.expression, result.result);
    }

    setWaitingForOperand(true);
    setOperator(nextOperator);
  };

  const handleEquals = () => {
    if (!operator || prevValue === null) return;

    const result = calculate(prevValue, display, operator);
    if (result.error) {
      setDisplay(result.error);
    } else {
      setDisplay(result.result);
      addToHistory(result.expression, result.result);
    }
    setPrevValue(null);
    setOperator(null);
    setWaitingForOperand(true);
  };

  const unaryOperations = {
    percent: { label: '%', fn: (n) => n / 100, desc: '百分数' },
    abs: { label: '|x|', fn: (n) => Math.abs(n), desc: '绝对值' },
    sqrt: { label: '√', fn: (n) => n < 0 ? NaN : Math.sqrt(n), desc: '平方根' },
    factorial: { label: 'n!', fn: (n) => factorial(n), desc: '阶乘' },
    ln: { label: 'ln', fn: (n) => n <= 0 ? NaN : Math.log(n), desc: '自然对数' },
    log10: { label: 'log', fn: (n) => n <= 0 ? NaN : Math.log10(n), desc: '常用对数' },
    exp: { label: 'eˣ', fn: (n) => Math.exp(n), desc: '自然指数' },
    reciprocal: { label: '1/x', fn: (n) => n === 0 ? NaN : 1 / n, desc: '倒数' },
    ceil: { label: '⌈x⌉', fn: (n) => Math.ceil(n), desc: '向上取整' },
    floor: { label: '⌊x⌋', fn: (n) => Math.floor(n), desc: '向下取整' },
    sin: { label: 'sin', fn: (n) => Math.sin(n * Math.PI / 180), desc: '正弦' },
    cos: { label: 'cos', fn: (n) => Math.cos(n * Math.PI / 180), desc: '余弦' },
    tan: { label: 'tan', fn: (n) => Math.tan(n * Math.PI / 180), desc: '正切' },
    asin: { label: 'sin⁻¹', fn: (n) => Math.asin(n) * 180 / Math.PI, desc: '反正弦' },
    acos: { label: 'cos⁻¹', fn: (n) => Math.acos(n) * 180 / Math.PI, desc: '反余弦' },
    atan: { label: 'tan⁻¹', fn: (n) => Math.atan(n) * 180 / Math.PI, desc: '反正切' },
    square: { label: 'x²', fn: (n) => n * n, desc: '平方' },
    cube: { label: 'x³', fn: (n) => n * n * n, desc: '立方' },
    primeFactors: { label: '分解', fn: (n) => primeFactors(n), desc: '分解质因数', isSpecial: true },
    primesBetween: { label: '素数', fn: null, desc: '区间素数', isSpecial: true },
  };

  const factorial = (n) => {
    if (n < 0 || !Number.isInteger(n)) return NaN;
    if (n > 170) return Infinity;
    let result = 1;
    for (let i = 2; i <= n; i++) {
      result *= i;
    }
    return result;
  };

  const primeFactors = (n) => {
    if (!Number.isInteger(n) || n < 2) return NaN;
    const factors = [];
    let num = n;
    for (let i = 2; i <= Math.sqrt(num); i++) {
      while (num % i === 0) {
        factors.push(i);
        num /= i;
      }
    }
    if (num > 1) factors.push(num);
    return factors.join(' × ');
  };

  const performUnary = (key) => {
    const op = unaryOperations[key];
    if (!op) return;

    const num = parseFloat(display);
    
    if (key === 'primeFactors') {
      const result = primeFactors(Math.floor(num));
      if (isNaN(result)) {
        setDisplay('输入无效');
      } else {
        addToHistory(`分解 ${Math.floor(num)}`, result);
        setDisplay(result);
      }
      setWaitingForOperand(true);
      return;
    }

    if (key === 'primesBetween') {
      if (prevValue === null) {
        setPrevValue(display);
        setOperator('primesBetween');
        setWaitingForOperand(true);
        return;
      }
    }

    const result = op.fn(num);
    if (isNaN(result)) {
      setDisplay('输入无效');
    } else {
      addToHistory(`${op.desc}(${num})`, formatResult(result));
      setDisplay(formatResult(result));
    }
    setWaitingForOperand(true);
  };

  const [primesResult, setPrimesResult] = useState(null);

  const findPrimesBetween = () => {
    if (prevValue === null) return;
    const a = Math.floor(parseFloat(prevValue));
    const b = Math.floor(parseFloat(display));
    const min = Math.min(a, b);
    const max = Math.max(a, b);
    
    if (min < 2 || max < 2 || min === max) {
      setPrimesResult('输入无效');
      return;
    }

    const primes = [];
    for (let i = min; i <= max; i++) {
      if (isPrime(i)) primes.push(i);
    }
    
    const result = primes.length > 0 ? primes.join(', ') : '无素数';
    setPrimesResult(result);
    addToHistory(`素数 ${min}~${max}`, `共${primes.length}个`);
  };

  const isPrime = (n) => {
    if (n < 2) return false;
    if (n === 2) return true;
    if (n % 2 === 0) return false;
    for (let i = 3; i <= Math.sqrt(n); i += 2) {
      if (n % i === 0) return false;
    }
    return true;
  };

  const clearHistory = () => {
    setHistory([]);
  };

  const constants = {
    pi: { label: 'π', value: Math.PI },
    e: { label: 'e', value: Math.E },
  };

  const inputConstant = (key) => {
    setDisplay(String(constants[key].value));
    setWaitingForOperand(true);
  };

  const binaryOpsScientific = [
    { key: 'pow', label: 'xʸ', op: '^' },
    { key: 'mod', label: 'mod', op: 'mod' },
    { key: 'gcd', label: 'gcd', op: 'gcd' },
    { key: 'lcm', label: 'lcm', op: 'lcm' },
    { key: 'avg', label: 'avg', op: 'avg' },
  ];

  const unaryRow1 = ['sqrt', 'square', 'cube', 'reciprocal'];
  const unaryRow2 = ['sin', 'cos', 'tan', 'ln'];
  const unaryRow3 = ['asin', 'acos', 'atan', 'log10'];
  const unaryRow4 = ['abs', 'ceil', 'floor', 'factorial'];
  const unaryRow5 = ['exp', 'percent', 'primeFactors', 'primesBetween'];

  return (
    <div className="page-container calculator-page">
      <h2 className="section-title" style={{ fontSize: 20, marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span><Icon name="icon-calc" size={20} /> 科学计算器</span>
        <button className="calc-history-btn" onClick={() => setShowHistory(!showHistory)}>
          <Icon name="icon-clipboard" size={18} /> 历史
        </button>
      </h2>

      <div className="calculator-wrapper">
        <div className={`calculator ${showHistory ? 'with-history' : ''}`}>
          <div className="calc-display">
            <div className="calc-expression">
              {prevValue !== null && operator && (
                <span>{prevValue} {operator === 'primesBetween' ? '素数区间' : operator}</span>
              )}
            </div>
            <div className="calc-value">{display}</div>
          </div>

          <div className="calc-mode-switch">
            <button 
              className={mode === 'standard' ? 'active' : ''}
              onClick={() => setMode('standard')}
            >
              标准
            </button>
            <button 
              className={mode === 'scientific' ? 'active' : ''}
              onClick={() => setMode('scientific')}
            >
              科学
            </button>
          </div>

          {mode === 'scientific' && (
            <div className="calc-scientific">
              <div className="calc-row">
                {unaryRow1.map(key => (
                  <button key={key} className="calc-btn func" onClick={() => performUnary(key)} title={unaryOperations[key].desc}>
                    {unaryOperations[key].label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {unaryRow2.map(key => (
                  <button key={key} className="calc-btn func" onClick={() => performUnary(key)} title={unaryOperations[key].desc}>
                    {unaryOperations[key].label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {unaryRow3.map(key => (
                  <button key={key} className="calc-btn func" onClick={() => performUnary(key)} title={unaryOperations[key].desc}>
                    {unaryOperations[key].label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {unaryRow4.map(key => (
                  <button key={key} className="calc-btn func" onClick={() => performUnary(key)} title={unaryOperations[key].desc}>
                    {unaryOperations[key].label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {unaryRow5.map(key => (
                  <button key={key} className="calc-btn func" onClick={() => performUnary(key)} title={unaryOperations[key].desc}>
                    {unaryOperations[key].label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {binaryOpsScientific.map(({ key, label, op }) => (
                  <button key={key} className="calc-btn func" onClick={() => performOperation(op)} title={label}>
                    {label}
                  </button>
                ))}
              </div>
              <div className="calc-row">
                {Object.entries(constants).map(([key, { label }]) => (
                  <button key={key} className="calc-btn const" onClick={() => inputConstant(key)}>
                    {label}
                  </button>
                ))}
                <button className="calc-btn func" onClick={toggleSign}>±</button>
                <button className="calc-btn func" onClick={findPrimesBetween} title="计算区间素数">
                  素数列表
                </button>
              </div>
            </div>
          )}

          <div className="calc-buttons">
            <div className="calc-row">
              <button className="calc-btn clear" onClick={clearAll}>AC</button>
              <button className="calc-btn clear" onClick={clearEntry}>CE</button>
              <button className="calc-btn func" onClick={backspace}>⌫</button>
              <button className="calc-btn op" onClick={() => performOperation('÷')}>÷</button>
            </div>
            <div className="calc-row">
              <button className="calc-btn num" onClick={() => inputDigit(7)}>7</button>
              <button className="calc-btn num" onClick={() => inputDigit(8)}>8</button>
              <button className="calc-btn num" onClick={() => inputDigit(9)}>9</button>
              <button className="calc-btn op" onClick={() => performOperation('×')}>×</button>
            </div>
            <div className="calc-row">
              <button className="calc-btn num" onClick={() => inputDigit(4)}>4</button>
              <button className="calc-btn num" onClick={() => inputDigit(5)}>5</button>
              <button className="calc-btn num" onClick={() => inputDigit(6)}>6</button>
              <button className="calc-btn op" onClick={() => performOperation('-')}>−</button>
            </div>
            <div className="calc-row">
              <button className="calc-btn num" onClick={() => inputDigit(1)}>1</button>
              <button className="calc-btn num" onClick={() => inputDigit(2)}>2</button>
              <button className="calc-btn num" onClick={() => inputDigit(3)}>3</button>
              <button className="calc-btn op" onClick={() => performOperation('+')}>+</button>
            </div>
            <div className="calc-row">
              <button className="calc-btn num zero" onClick={() => inputDigit(0)}>0</button>
              <button className="calc-btn num" onClick={inputDecimal}>.</button>
              <button className="calc-btn equals" onClick={handleEquals}>=</button>
            </div>
          </div>

          {primesResult && (
            <div className="calc-primes-result">
              <div className="primes-title">素数列表：</div>
              <div className="primes-content">{primesResult}</div>
              <button className="primes-close" onClick={() => setPrimesResult(null)}>关闭</button>
            </div>
          )}
        </div>

        {showHistory && (
          <div className="calc-history-panel">
            <div className="history-header">
              <span>计算历史</span>
              <button onClick={clearHistory}>清空</button>
            </div>
            <div className="history-list">
              {history.length === 0 ? (
                <div className="history-empty">暂无历史记录</div>
              ) : (
                history.map((item, idx) => (
                  <div key={idx} className="history-item" onClick={() => setDisplay(String(item.result))}>
                    <div className="history-expr">{item.expression}</div>
                    <div className="history-result">= {item.result}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      <div className="calc-help">
        <h3 style={{ fontSize: 16, marginBottom: 12, color: 'var(--text-h)' }}>功能说明</h3>
        <div className="help-grid">
          <div className="help-col">
            <h4>单目运算</h4>
            <ul>
              <li><b>√</b> 平方根</li>
              <li><b>x²</b> 平方</li>
              <li><b>x³</b> 立方</li>
              <li><b>1/x</b> 倒数</li>
              <li><b>|x|</b> 绝对值</li>
              <li><b>⌈x⌉</b> 向上取整</li>
              <li><b>⌊x⌋</b> 向下取整</li>
              <li><b>n!</b> 阶乘</li>
            </ul>
          </div>
          <div className="help-col">
            <h4>三角函数</h4>
            <ul>
              <li><b>sin / cos / tan</b> 正弦/余弦/正切</li>
              <li><b>sin⁻¹ / cos⁻¹ / tan⁻¹</b> 反三角函数</li>
              <li><b>ln</b> 自然对数</li>
              <li><b>log</b> 常用对数</li>
              <li><b>eˣ</b> 自然指数</li>
              <li><b>%</b> 百分数</li>
              <li><b>π / e</b> 常数</li>
            </ul>
          </div>
          <div className="help-col">
            <h4>双目运算</h4>
            <ul>
              <li><b>+ − × ÷</b> 四则运算</li>
              <li><b>xʸ</b> 乘方</li>
              <li><b>mod</b> 取余</li>
              <li><b>gcd</b> 最大公约数</li>
              <li><b>lcm</b> 最小公倍数</li>
              <li><b>avg</b> 平均数</li>
              <li><b>分解</b> 分解质因数</li>
              <li><b>素数</b> 区间素数</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalculatorPage;
