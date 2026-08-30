<script lang="ts">
	import type { HTMLTableAttributes } from 'svelte/elements';
	import { cn, type WithElementRef } from '$lib/utils.js';

	let {
		ref = $bindable(null),
		class: className,
		containerClass = 'relative w-full overflow-x-auto',
		children,
		...restProps
	}: WithElementRef<HTMLTableAttributes> & { containerClass?: string } = $props();
</script>

<!-- The container defaults to its own scroll context. Pass `containerClass`
     to opt out: `overflow-x: auto` forces `overflow-y` to compute to `auto`
     too, which makes this div the containing block for any sticky header
     inside, and it never scrolls. -->
<div data-slot="table-container" class={containerClass}>
	<table
		bind:this={ref}
		data-slot="table"
		class={cn('w-full caption-bottom text-xs', className)}
		{...restProps}
	>
		{@render children?.()}
	</table>
</div>
