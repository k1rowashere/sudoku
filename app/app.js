const gameState = {
  selectedCells: new Set(),
  incorrectCells: new Set(),
  isMultiSelecting: false,
  currentMode: () => document.querySelector('input[name="sudoku-mode"]:checked').value,
  undoList: [],
  redoList: [],
};

function handleInput(cells, number, currentMode = gameState.currentMode()) {
  if (number < 0 || number > 9) return;
  let toUndo = [];

  cells.forEach(cell => {
    const solutionEl = cell.children[0];
    const pencilMarkEl = cell.children[1];

    gameState.incorrectCells.delete(cell);
    cell.classList.remove('bg-red-200');

    add_move(toUndo, cell);

    if (number === 0) {
      if (cell.classList.contains('given-clue')) {
        if (currentMode === 'edit') {
          cell.classList.remove('given-clue');
          solutionEl.textContent = '';
        }
      } else if (solutionEl.textContent !== '')
        solutionEl.textContent = '';
      else
        for (let i = 0; i < 9; i++)
          pencilMarkEl.children[i].classList.add('invisible');
    } else {
      switch (currentMode) {
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
    }
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

  gameState.incorrectCells.delete(cell);
  cell.classList.remove('bg-red-200');

  cell.classList.toggle('given-clue', move.given);
  solutionEl.textContent = move.value;

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

function importString(str) {
  for (let i = 0; i < 9; i++)
    for (let j = 0; j < 9; j++) {
      const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)
      const solutionEl = cell.children[0];

      const val = str[i * 9 + j];

      if (val === '.' || val === '0') {
        solutionEl.textContent = '';
      } else if ('0' <= val && val <= '9') {
        solutionEl.textContent = val;
        cell.classList.add('given-clue');
      } else if (val === undefined) {
        console.error(`Invalid sudoku string length: ${str.length}`);
        alert(`Invalid sudoku string length: ${str.length}`);
        return;
      } else {
        console.error(`Invalid character "${val}" in sudoku string`);
        alert(`Invalid character "${val}" in sudoku string`);
        return;
      }
    }
}

function exportString() {
  let given = ""
  let solution = "";

  for (let i = 0; i < 9; i++)
    for (let j = 0; j < 9; j++) {
      const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)

      if (cell.classList.contains('given-clue')) {
        given += cell.children[0].textContent || '.';
        solution += cell.children[0].textContent || '.';
      } else {
        given += '.'
        solution += cell.children[0].textContent || '.';
      }

    }
  return {given, player_solution: solution}
}


function solve() {
  eel.solve_sudoku(exportString().given)(function (result) {
    const {status, solution} = result;

    // TODO: print status (solved, unsolved, invalid)
    for (let i = 0; i < 9; i++)
      for (let j = 0; j < 9; j++) {
        const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)

        if (!cell.classList.contains('given-clue')) {
          const val = solution[i][j];
          if ((val & val - 1) === 0)  // only one bit set
            handleInput([cell], Math.log2(val) + 1, 'final');
          else
            for (let k = 0; k < 9; k++) // pencil marks
              if (val & (1 << k))
                handleInput([cell], k + 1, 'pencil');
        }
      }
  });
}

function checkSolution() {
  const given = exportString().given;
  eel.solve_sudoku(given)(function (result) {
    const {status, solution} = result;
    let incorrect = false;
    let incomplete = false;

    for (let i = 0; i < 9; i++) {
      for (let j = 0; j < 9; j++) {
        const cell = document.querySelector(`.sudoku-cell[data-row="${i}"][data-col="${j}"]`)
        const val = cell.children[0].textContent;
        const sol = solution[i][j];
        incomplete |= val === '';

        // value is set and not in solution domain
        if (val && (1 << (val - 1) & sol) === 0) {
          cell.classList.add('bg-red-200');
          gameState.incorrectCells.add(cell);
          incorrect = true
        }
      }
    }

    if (incorrect)
      alert("Incorrect solution!");
    else if (incomplete)
      alert("Looks good so far!");
    else
      alert("Correct solution!");
  });
}

function generatePuzzle(emptyCount) {
  eel.generate(emptyCount)(importString);
}


document.addEventListener('DOMContentLoaded', function () {
  const numButtons = document.querySelectorAll('.num-btn');
  const sudokuCells = document.querySelectorAll('.sudoku-cell');
  const clearButton = document.getElementById('backspace-btn')
  const undoButton = document.getElementById('undo-btn');
  const redoButton = document.getElementById('redo-btn');


  const solveButton = document.getElementById('solve-btn');
  const clearAllButton = document.getElementById('clear-all-btn');
  const checkButton = document.getElementById('check-btn');


  const importInput = document.getElementById('load-string');
  const importButton = document.getElementById('import-btn');
  const exportButton = document.getElementById('export-btn');


  const generateButton = document.getElementById('generate-btn')
  const difficultySelector = document.getElementById('difficulty')

  clearButton.addEventListener('click', () => handleInput(gameState.selectedCells, 0));
  undoButton.addEventListener('click', () => handleUndoRedo(gameState.undoList, gameState.redoList));
  redoButton.addEventListener('click', () => handleUndoRedo(gameState.redoList, gameState.undoList));

  solveButton.addEventListener('click', () => {
    handleInput(sudokuCells, 0); // clear the board
    solve();
  });
  clearAllButton.addEventListener('click', () => handleInput(sudokuCells, 0));
  checkButton.addEventListener('click', checkSolution);


  importButton.addEventListener('click', () => {
    handleInput(sudokuCells, 0, 'edit'); // clear the board
    importString(importInput.value, true)
  });

  exportButton.addEventListener('click', async () => {
    const sudoku = exportString().given;
    importInput.value = sudoku;
    await navigator.clipboard.writeText(sudoku);
  });

  numButtons.forEach(button => {
    button.addEventListener('click', function () {
      const number = parseInt(this.dataset.value);
      handleInput(gameState.selectedCells, number);
    });
  });

  generateButton.addEventListener('click', () => {
    handleInput(sudokuCells, 0, 'edit'); // clear the board
    switch (difficultySelector.value) {
      case 'easy':
        generatePuzzle(81 - 45);
        break;
      case 'medium':
        generatePuzzle(81 - 30);
        break;
      case 'hard':
        generatePuzzle(81 - 17);
        break;
    }
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
      // unfocus other elements (inputs, buttons, etc.)
      if (document.activeElement.tagName !== 'BODY') {
        document.activeElement.blur();
      }

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
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
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
      handleInput(gameState.selectedCells, parseInt(e.key));
    }
    // Backspace/Delete to clear
    else if (e.key === 'Backspace' || e.key === 'Delete') {
      handleInput(gameState.selectedCells, 0);
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
          cell.classList.remove('!bg-blue-200');
          newCell.classList.add('!bg-blue-200');
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
