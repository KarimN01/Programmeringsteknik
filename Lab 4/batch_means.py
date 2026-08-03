import math

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def parse_float(value):
    """Parse a numeric value and reject malformed entries"""
    cleaned = value.strip()
    if not cleaned:
        return None

    # Accept only standard floating-point syntax so malformed values such as
    # "-0.O1" are treated as invalid input and trigger a warning.
    if not all(ch.isdigit() or ch in '-+.eE' for ch in cleaned):
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def sort_batches(item):
    """Return a sort key that orders batches numerically when possible."""
    batch = item[0]
    try:
        return (0, int(batch))
    except ValueError:
        return (1, batch)


def load_data(filename):
    """Read the CSV file, group the measurements by batch, and skip bad rows."""
    data = {}

    try:
        with open(filename, 'r', encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue

                parts = [part.strip() for part in line.split(',')]
                if len(parts) != 4:
                    print(f'Warning: wrong input format for entry: {line}')
                    continue

                batch = parts[0]
                x = parse_float(parts[1])
                y = parse_float(parts[2])
                value = parse_float(parts[3])

                if x is None or y is None or value is None:
                    print(f'Warning: wrong input format for entry: {line}')
                    continue

                data.setdefault(batch, []).append((x, y, value))
    except FileNotFoundError:
        print(f'Sorry, I could not find the file "{filename}". Please check the filename and try again.')
        return {}

    return data


def compute_batch_averages(data):
    """Compute the average value for each batch from points inside the unit circle."""
    averages = {}

    for batch, sample in sorted(data.items(), key=sort_batches):
        total = 0.0
        count = 0

        for x, y, value in sample:
            if x * x + y * y <= 1:
                total += value
                count += 1

        averages[batch] = total / count if count else None

    return averages


def print_batch_averages(averages):
    """Print the computed batch averages."""
    print('Batch Average')
    for batch, average in sorted(averages.items(), key=sort_batches):
        if average is None:
            print(f'{batch} No valid points')
        else:
            print(f'{batch} {average}')


def plot_data(data, f):
    """Plot the loaded measurements and save the result as a PDF file.
    """
    fig, ax = plt.subplots(figsize=(6, 6))
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
              'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
              'tab:olive', 'tab:cyan']
    color_map = {}

    angles = [i / 150 * 2 * math.pi for i in range(151)]
    x_coords = [math.cos(angle) for angle in angles]
    y_coords = [math.sin(angle) for angle in angles]
    ax.plot(x_coords, y_coords, color='black', linestyle='--', linewidth=1)

    if data is not None:
        for batch, sample in sorted(data.items(), key=sort_batches):
            color = color_map.setdefault(batch, colors[len(color_map) % len(colors)])
            for x, y, value in sample:
                ax.scatter(x, y, color=color, s=25)
                ax.annotate(str(value), (x, y), textcoords='offset points', xytext=(3, 3), fontsize=8)

    ax.set_aspect('equal', 'box')
    ax.set_title('Batch data')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.grid(True, alpha=0.3)

    output_name = f.rsplit('.', 1)[0] + '.pdf'
    plt.savefig(output_name)
    plt.close(fig)


def show_results(data, filename):
    """Compute, print, and plot the results for a file."""
    averages = compute_batch_averages(data)
    print_batch_averages(averages)
    plot_data(data, filename)
    print(f'A plot of the data can be found in {filename.rsplit(".", 1)[0]}.pdf')


def main():
    """Main body of the program."""
    filename = input('Which csv file should be analyzed? ').strip()
    data = load_data(filename)
    if not data:
        return

    show_results(data, filename)


if __name__ == '__main__':
    main()
