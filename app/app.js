const gameState = {
  selectedCells: new Set(),
  isMultiSelecting: false,
  currentMode: () => document.querySelector('input[name="sudoku-mode"]:checked').value,
};

document.addEventListener('DOMContentLoaded', function () {
  const numButtons = document.querySelectorAll('.num-btn');
  const sudokuCells = document.querySelectorAll('.sudoku-cell');


  // Function to clear all selections
  // Handle number input based on current mode
  function handleNumberInput(number) {
    gameState.selectedCells.forEach(cell => {
      if (gameState.currentMode() === 'final') {
        // Set final number
        // You'll need to implement this based on your cell structure
        setFinalNumber(cell, number);
      } else if (gameState.currentMode() === 'pencil') {
        // Toggle pencil mark
        togglePencilMark(cell, number);
      } else if (gameState.currentMode() === 'edit') {
        // Edit given clue
        setGivenClue(cell, number);
      }
    });
  }

  // Handle clear input
  function handleClearInput() {
    gameState.selectedCells.forEach(cell => {
      if (gameState.currentMode() === 'final') {
        clearFinalNumber(cell);
      } else if (gameState.currentMode() === 'pencil') {
        clearPencilMarks(cell);
      } else if (gameState.currentMode() === 'edit') {
        clearGivenClue(cell);
      }
    });
  }

  // Placeholder functions - implement these based on your cell structure
  function setFinalNumber(cell, number) {
    // Find or create the player solution element in the cell
    let solutionEl = cell.querySelector('.player-solution');
    if (!solutionEl) {
      solutionEl = document.createElement('div');
      solutionEl.className = 'player-solution';
      cell.appendChild(solutionEl);
    }
    solutionEl.textContent = number;
  }

  function clearFinalNumber(cell) {
    const solutionEl = cell.querySelector('.player-solution');
    if (solutionEl) {
      solutionEl.remove();
    }
  }

  function togglePencilMark(cell, number) {
    const pencilMarks = cell.querySelector('.pencil-marks');
    if (!pencilMarks) return;

    const markEl = pencilMarks.querySelector(`.pm_${number}`);
    if (markEl) {
      // Remove existing mark
      markEl.remove();
    } else {
      // Add new mark
      // You'll need to determine position based on your pencil marks grid
      const newMark = document.createElement('div');
      newMark.className = `pencil-mark pm_${number}`;
      newMark.textContent = number;
      // Append to correct position in the 3x3 grid
      // This depends on your pencil marks implementation
      pencilMarks.appendChild(newMark);
    }
  }


  // Selection
  sudokuCells.forEach(cell => {
    const classes = ['!bg-blue-200', '!border-blue-500'];
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
  document.addEventListener('keydown', function (e) {
    if (gameState.selectedCells.size === 0) return;

    // Number keys 1-9
    if (e.key >= '1' && e.key <= '9') {
      const number = parseInt(e.key);
      handleNumberInput(number);
    }
    // Backspace/Delete to clear
    else if (e.key === 'Backspace' || e.key === 'Delete') {
      handleClearInput();
    }
  });
});
