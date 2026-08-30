<script lang="ts">
	import type { ComponentProps } from 'svelte';
	import ArrowDownIcon from '@lucide/svelte/icons/arrow-down';
	import ArrowUpDownIcon from '@lucide/svelte/icons/arrow-up-down';
	import ArrowUpIcon from '@lucide/svelte/icons/arrow-up';
	import { Button } from '$lib/components/ui/button/index.js';

	type Props = ComponentProps<typeof Button> & {
		/** TanStack's `column.getIsSorted()`: 'asc', 'desc', or false for unsorted. */
		sorted?: 'asc' | 'desc' | false;
	};

	let { variant = 'ghost', size = 'sm', sorted = false, ...restProps }: Props = $props();

	// Unsorted is the original item order, which is meaningful here -- Python
	// preserves the order it was given -- so it needs to be a visibly distinct
	// third state rather than just "not highlighted".
	const label = $derived(
		sorted === 'asc'
			? 'Sorted A to Z, click to reverse'
			: sorted === 'desc'
				? 'Sorted Z to A, click to restore original order'
				: 'Unsorted, click to sort A to Z'
	);
</script>

<Button {variant} {size} title={label} aria-label={label} {...restProps}>
	Item
	{#if sorted === 'asc'}
		<ArrowUpIcon class="ms-2 size-4 text-muted-foreground" />
	{:else if sorted === 'desc'}
		<ArrowDownIcon class="ms-2 size-4 text-muted-foreground" />
	{:else}
		<ArrowUpDownIcon class="ms-2 size-4 text-muted-foreground" />
	{/if}
</Button>
