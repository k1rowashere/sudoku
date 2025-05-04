const gameState = {
  selectedCells: new Set(),
  isMultiSelecting: false,
  currentMode: () => document.querySelector('input[name="sudoku-mode"]:checked').value,
  undoList: [],
  redoList: [],
};

function handleNumberInput(number) {
  if (number < 1 || number > 9) return;
  let toUndo = [];

  gameState.selectedCells.forEach(cell => {
    const solutionEl = cell.children[0];
    const pencilMarkEl = cell.children[1];

    add_move(toUndo, cell);

    switch (gameState.currentMode()) {
      case 'final':
        if (!cell.classList.contains('given-clue'))
          solutionEl.textContent = number;
        break;
      case 'pencil':
        pencilMarkEl.children[number - 1].classList.toggle('invisible');
        break;
      case 'edit':
        solutionEl.textContent = number;
        cell.classList.add('given-clue');
        break;
    }
  });

  if (toUndo.length > 0) {
    gameState.redoList = [];
    gameState.undoList.push(toUndo);
  }
}

function handleClearInput() {
  let toUndo = [];
  gameState.selectedCells.forEach(cell => {
    const solutionEl = cell.children[0];
    const pencilMarkEl = cell.children[1];

    add_move(toUndo, cell);

    if (cell.classList.contains('given-clue')) {
      if (gameState.currentMode() === 'edit') {
        cell.classList.remove('given-clue');
        solutionEl.textContent = '';
      }
      return;
    }
    // otherwise, remove final, if no final then remove pencil marks
    if (solutionEl.textContent !== '')
      solutionEl.textContent = '';
    else
      for (let i = 0; i < 9; i++)
        pencilMarkEl.children[i].classList.add('invisible');
  });

  if (toUndo.length > 0) {
    gameState.redoList = [];
    gameState.undoList.push(toUndo);
  }
}

// Undo and Redo
function add_move(toUndo, cell) {
  toUndo.push({
    cell: cell,
    value: cell.children[0].textContent,
    given: cell.classList.contains('given-clue'),
    pencilMarks: [...Array.from(cell.children[1].children).map(el => !el.classList.contains('invisible'))]
  });
}

function apply_move(move) {
  const cell = move.cell;
  const solutionEl = cell.children[0];
  const pencilMarkEl = cell.children[1];

  solutionEl.textContent = move.value;

  cell.classList.toggle('given-clue', move.given);

  for (let i = 0; i < 9; i++)
    pencilMarkEl.children[i].classList.toggle('invisible', !move.pencilMarks[i]);
}

function handleUndoRedo(l1, l2) {
  if (l1.length === 0) return;
  const todo = l1.pop();

  const curr = []

  todo.forEach((todo) => {
    add_move(curr, todo.cell)
    apply_move(todo);
  });

  l2.push(curr);
}

function load_string(str, given = false) {
  for (let i = 0; i < 9; i++)
    for (let j = 0; j < 9; j++) {
      const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)
      const solutionEl = cell.children[0];

      if (!cell.classList.contains('given-clue') || given) {
        const val = str[i * 9 + j];
        if (val === '.' || val === '0') {
          solutionEl.textContent = '';
        } else if ('0' <= val || val <= '9') {
          solutionEl.textContent = val;
          if (given)
            cell.classList.add('given-clue');
        }
      }
    }
}


function solve() {
  let sudoku = ""

  for (let i = 0; i < 9; i++)
    for (let j = 0; j < 9; j++) {
      const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)

      if (cell.classList.contains('given-clue'))
        sudoku += cell.children[0].textContent || '.';
      else
        sudoku += '.'
    }

  // call function from python using eel
  eel.solve_sudoku(sudoku)(function (sudoku) {
    console.log(sudoku);
    load_string(sudoku);
  });
}


document.addEventListener('DOMContentLoaded', function () {
  const numButtons = document.querySelectorAll('.num-btn');
  const sudokuCells = document.querySelectorAll('.sudoku-cell');
  const clearButton = document.getElementById('backspace-btn')
  const undoButton = document.getElementById('undo-btn');
  const redoButton = document.getElementById('redo-btn');
  const solveButton = document.getElementById('solve-btn');

  clearButton.addEventListener('click', handleClearInput);
  undoButton.addEventListener('click', () => handleUndoRedo(gameState.undoList, gameState.redoList));
  redoButton.addEventListener('click', () => handleUndoRedo(gameState.redoList, gameState.undoList));
  solveButton.addEventListener('click', solve);
  numButtons.forEach(button => {
    button.addEventListener('click', function () {
      const number = parseInt(this.dataset.value);
      handleNumberInput(number);
    });
  });

  // Selection
  sudokuCells.forEach(cell => {
    const classes = ['!bg-blue-200'];
    const add = (cell) => {
      cell.classList.add(...classes);
      gameState.selectedCells.add(cell);
    }
    const remove = (cell) => {
      cell.classList.remove(...classes);
      gameState.selectedCells.delete(cell);
    }

    cell.addEventListener('mousedown', e => {
      e.preventDefault();

      if (!gameState.isMultiSelecting) {
        if (!e.ctrlKey && !e.metaKey)
          gameState.selectedCells.forEach(remove);

        gameState.isMultiSelecting = true;
      }

      if (gameState.selectedCells.has(cell))
        remove(cell);
      else
        add(cell);
    });

    cell.addEventListener('mouseenter', () => {
      if (gameState.isMultiSelecting) add(cell)
    });
  });

  document.addEventListener('mouseup', function () {
    gameState.isMultiSelecting = false;
  });

  // Keyboard shortcuts for number input
  let originalMode = gameState.currentMode();
  let controlHeld = false;

  document.addEventListener('keydown', e => {
    if (e.key === 'Control' || e.key === 'Meta') {
      controlHeld = true;
      originalMode = gameState.currentMode();
      const pencilInput = document.querySelector('input[name="sudoku-mode"][value="pencil"]');
      if (pencilInput) {
        pencilInput.checked = true;
      }
    }

    if (gameState.selectedCells.size === 0) return;
    // Number keys 1-9
    if (e.key >= '1' && e.key <= '9') {
      handleNumberInput(parseInt(e.key));
    }
    // Backspace/Delete to clear
    else if (e.key === 'Backspace' || e.key === 'Delete') {
      handleClearInput();
    }
    // arrow keys
    else if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
      if (gameState.selectedCells.size === 1) {
        const direction = {
          ArrowUp: [-1, 0],
          ArrowDown: [1, 0],
          ArrowLeft: [0, -1],
          ArrowRight: [0, 1],
          ' ': [0, 1]
        }[e.key];
        const cell = gameState.selectedCells.values().next().value;
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        let newRow = row + direction[0];
        let newCol = col + direction[1];
        if (newRow < 0) newCol--;
        if (newCol < 0) newRow--;
        if (newRow > 8) newCol++;
        if (newCol > 8) newRow++;

        const selector = `.sudoku-cell[data-row="${(newRow % 9 + 9) % 9}"][data-col="${(newCol % 9 + 9) % 9}"]`;
        const newCell = document.querySelector(selector);
        if (newCell) {
          cell.classList.remove('!bg-blue-200', '!border-blue-500');
          newCell.classList.add('!bg-blue-200', '!border-blue-500');
          gameState.selectedCells.clear();
          gameState.selectedCells.add(newCell);
        }
      }
    }

  });

  // shift switches to pencil mode, but switches back to original mode when released
  document.addEventListener('keyup', e => {
    if (e.key === 'Control' || e.key === 'Meta') {
      if (controlHeld) {
        controlHeld = false;

        const originalModeInput = document.querySelector(`input[name="sudoku-mode"][value="${originalMode}"]`);
        if (originalModeInput) {
          originalModeInput.checked = true;
        }
      }
    }
  });
});
